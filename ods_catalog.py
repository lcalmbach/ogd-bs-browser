import streamlit as st
import requests
import pandas as pd
import io
import locale
import webbrowser
from dataclasses import dataclass
import boto3
from boto3.dynamodb.conditions import Key
import socket
import configparser

from tools import *
from text import *
from config import *


locale.setlocale(locale.LC_ALL, "")
cfg = configparser.ConfigParser()
cfg.read('aws_credentials.cfg')

hostname = socket.gethostname()
if hostname.lower() == 'liestal':
    aws_access_key_id = cfg['default']['aws_access_key_id']
    aws_secret_access_key = cfg['default']['aws_secret_access_key']
else:
    aws_access_key_id = st.secrets['aws_access_key_id']
    aws_secret_access_key = st.secrets['aws_secret_access_key']
dynamodb = boto3.client(
    "dynamodb",
    region_name="eu-central-1",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)


class Subscription:
    """
    see: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html
    """

    def __init__(self, email, catalog):
        self.table_name = "ods_subscription"
        self.email = email
        self.catalog = catalog
    
    @property
    def dynamodb_table(self):
        dynamodb_resource = boto3.resource(
            "dynamodb",
            region_name="eu-central-1",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        return dynamodb_resource.Table(self.table_name)

    def unsubscribe(self):
        response = self.dynamodb_table.delete_item(Key={"email": self.email, "catalog": self.catalog})
        st.success(f"You were successfully unsuscribed to the catalog {self.catalog}")

    def subscribe(self):
        created_date = datetime.now().strftime(FORMAT_YMD_HM)
        item = {
            "email": {"S": self.email},
            "catalog": {"S": self.catalog},
            "created_date": {"S": created_date},
        }
        response = dynamodb.put_item(TableName="ods_subscription", Item=item)
        st.success(f"You were successfully suscribed to the catalog {self.catalog}")

    def has_subscription(self):
        response = self.dynamodb_table.get_item(Key={"email": self.email, "catalog": self.catalog})
        return "Item" in response


class Catalog:
    def __init__(self, base):
        self.base = base
        self.providers = st.session_state["providers_dict"]
        self.datasets = self.get_datasets()
        self.current_dataset = Dataset(self.datasets.iloc[0], self)
        self.fields = []
        self.all_themes, self.dataset_theme = self.get_themes()
        self.value_fields = []
        self.filters = []
        self.agg_func = SUMMARY_FUNCTIONS[0]
        self.filter_expression = ""

    def display_info_page(self):
        self.providers = sort_dict(self.providers, 1)
        list = [f"<li>[{self.providers[x]}]({x})</li>" for x in self.providers.keys()]
        list = [f'<li><a href="{x}">{self.providers[x]}</a></li>' for x in self.providers.keys()]
        list = "".join(list)
        list = f"<ul>{list}</ul><p><p>"
        st.markdown(about.format(len(self.providers), list), unsafe_allow_html=True)

    def save_to_db(self, email_address, info_new_datasets, dataset_to_add):
        created_date = datetime.now().strftime(FORMAT_YMD_HM)
        for dataset in dataset_to_add:
            catalog_dataset = f"{self.base}/{dataset}"
            item = {
                "email": {"S": email_address},
                "catalog": {"S": self.base},
            }
            response = dynamodb.put_item(TableName="ods_subscription", Item=item)

    def subscribe(self):
        st.markdown("## Subscribe for Update Notifications")
        st.markdown(
            f"Enter your email and check the checkbox below if you wish to be notified when the provider **{self.providers[self.base]}** publishes a new dataset."
        )

        st.session_state["email_address"] = st.text_input("Email", value=st.session_state["email_address"])
        if st.session_state["email_address"] != '':
            subscription = Subscription(st.session_state["email_address"], self.base)
            info_new_datasets = st.checkbox(
                label="Send mail for new datasets in current catalog", value=True
            )
            if subscription.has_subscription():
                st.info(
                    "You already are subscribed to this provider, uncheck the checkbox above and press the `Execute` button to unscribe."
                )
            if st.button("Execute"):
                if subscription.has_subscription() and not info_new_datasets:
                    subscription.unsubscribe()
                elif not subscription.has_subscription() and info_new_datasets:
                    subscription.subscribe()

    def get_themes(self):
        themes = []
        dataset_theme = pd.DataFrame({"dataset_id": [], "theme": []})
        for index, row in self.datasets.iterrows():
            if row["themes"]:
                for item in row["themes"]:
                    themes.append(item)
                    df = pd.DataFrame({"dataset_id": [row["id"]], "theme": [item]})
                    dataset_theme = pd.concat([dataset_theme, df])
        themes = list(set(themes))
        themes.sort()
        return themes, dataset_theme

    def get_datasets(self):
        url = f"{self.base}/api/v2/catalog/exports/json?limit=-1&offset=0&timezone=UTC"
        response = requests.get(url)
        df = pd.DataFrame()
        if response.status_code == 200:
            data = response.json()
            if "dcat" in data[0]["metas"]:
                df = [
                    {
                        "id": x["dataset_id"],
                        "fields": x["fields"],
                        "title": x["metas"]["default"]["title"],
                        "description": x["metas"]["default"]["description"],
                        "themes": x["metas"]["default"]["theme"],
                        "issued": x["metas"]["dcat"]["issued"],
                    }
                    for x in data
                ]
            else:
                df = [
                    {
                        "id": x["dataset_id"],
                        "fields": x["fields"],
                        "title": x["metas"]["default"]["title"],
                        "description": x["metas"]["default"]["description"],
                        "themes": x["metas"]["default"]["theme"],
                        "issued": None,
                    }
                    for x in data
                ]

            df = pd.DataFrame(df)
        df["issued"] = pd.to_datetime(df["issued"], errors="coerce")
        return df

    def set_current_record(self):
        def filter_for_title(find_expression):
            df = self.datasets
            df = df[df["title"].str.contains(find_expression)]
            return df

        def filter_for_themes(df, themes_filter):
            _df = self.dataset_theme[self.dataset_theme["theme"].isin(themes_filter)]
            df = _df.set_index("dataset_id").join(df.set_index("id"), how="inner")
            df = df.reset_index()
            df = df.rename(columns={"index": "id"})
            df = df.drop("theme", axis=1)
            df.drop_duplicates(subset="id")
            return df

        def filter_for_dates(df, days):
            df["x"] = pd.to_datetime("today") - pd.to_timedelta(f"{days} day")
            _df = df[df["issued"] > df["x"]]
            return _df

        with st.expander("**Select a Dataset**", expanded=True):
            cols = st.columns(3)
            with cols[0]:
                title_filter = st.text_input("Title contains:")
            with cols[1]:
                themes_filter = st.multiselect(
                    "Dataset belongs to theme(s):", self.all_themes
                )
            with cols[2]:
                date_filter = st.number_input(
                    "Issued during last n days:", min_value=0, max_value=10000
                )
            df = self.datasets if title_filter == "" else filter_for_title(title_filter)
            if len(themes_filter) > 0:
                df = filter_for_themes(df, themes_filter)
            if date_filter > 0:
                df = filter_for_dates(df, date_filter)
            settings = get_table_settings(df)

            st.markdown(f"{self.providers[self.base]} has {len(df)} datasets")
            cols = [
                {
                    "name": "id",
                    "type": "str",
                    "hide": False,
                    "precision": 0,
                    "width": 100,
                },
                {
                    "name": "issued",
                    "hide": False,
                    "precision": 0,
                    "type": "date",
                    "width": 100,
                },
                {
                    "name": "title",
                    "hide": False,
                    "precision": 0,
                    "type": "str",
                    "width": 500,
                },
            ]
            response = show_table(df[["id", "title", "issued"]], cols, settings)
            if response:
                self.current_dataset = Dataset(
                    self.datasets[self.datasets["id"] == response["id"]].iloc[0], self
                )


class Dataset:
    def __init__(self, ds: dict, parent: Catalog):
        self.parent = parent
        self.id = ds["id"]
        self.title = ds["title"]
        self.description = (
            ds["description"].replace('p"', "p")
            if "description" in ds and ds["description"]
            else ""
        )

        if ds["fields"]:
            dict_fields = ds["fields"]
            self.fields_df = pd.DataFrame(dict_fields)[
                ["name", "description", "label", "type"]
            ]
        else:
            self.fields_df = pd.DataFrame(
                {"name": [], "description": [], "label": [], "type": []}
            )
        self.themes = ds["themes"] if "themes" in ds else ""
        self.record_count = self.get_record_count()
        self.query = Query(self, None)

    def get_record_count(self):
        url = f"{self.parent.base}/api/v2/catalog/datasets/{self.id}/records?limit=1&offset=0&timezone=UTC"
        count = 0
        try:
            response = requests.get(url)
            count = 0
            if response.status_code == 200:
                data = response.json()
                count = data["total_count"]
        except:
            st.warning(f"Record {self.id} has errors")
        return count

    def preview_data(self, rows):
        url = f"{self.parent.base}/api/v2/catalog/datasets/{self.id}/exports/csv/?limit={rows}&offset=0&timezone=UTC"
        response = requests.get(url)
        df = pd.read_csv(io.StringIO(response.text), sep=";")
        st.markdown(f"{self.record_count :n} records")
        st.write(df)
        show_download_button(df)

    def show_fields(self):
        df = pd.DataFrame(self.fields)
        df = df[["name", "description", "label", "type"]]
        st.write(df)

    def display_header(self):
        st.markdown(f"### {self.title}")
        tabs = st.tabs(["Description", "Preview", "Fields", "Gugus"])
        with tabs[0]:
            st.markdown(self.description, unsafe_allow_html=True)
        with tabs[1]:
            self.preview_data(MAX_PREVIEW_RECORDS)
        with tabs[2]:
            st.write(self.fields_df)

    def display_query_result(self):
        st.markdown(f"**Query dataset: {self.title}**")
        self.query.get_user_input()
        self.query.build_urls()
        with st.expander("URL"):
            st.markdown(f"```{self.query.url}```")
        cols = st.columns([1, 1, 4])
        show_table = False
        with cols[0]:
            is_disabled = (self.query.is_groupby) and (
                (len(self.query.group_fields) == 0)
                or (len(self.query.value_fields) == 0)
                or (len(self.query.agg_functions) == 0)
            )
            if st.button(
                "Show data",
                disabled=is_disabled,
                help="For aggregation queries group- and value-fields as well as at least one aggregation function are required",
            ):
                show_table = True
        with cols[1]:
            if not (self.query.is_groupby):
                if st.button("Export data"):
                    webbrowser.open_new_tab(self.query.url_export)
        if show_table:
            match_count = self.query.get_match_count()
            if match_count == 0:
                st.info("No records match the specified criteria")
            else:
                df, ok = self.query.get_data(match_count)
                if ok:
                    text = f"{match_count} matching records"
                    if len(df) < match_count:
                        text += f" (preview={len(df)})"
                    st.markdown(text)
                    st.write(df)
                    show_download_button(df)


@dataclass
class WhereExpression:
    field: int = 0
    comp: str = ""
    value: str = ""


class Query:
    def __init__(self, ds: object, json_query: str):
        self.ds: dict = ds
        self.is_groupby: bool = False
        self.all_fields_list: list = list(ds.fields_df["name"])
        self.group_fields_options: list = list(
            ds.fields_df[ds.fields_df["type"].isin(["text", "int", "date"])]["name"]
        )
        self.value_fields_options: list = list(
            ds.fields_df[ds.fields_df["type"] != "text"]["name"]
        )
        self.url: str = ""
        self.url_count: str = ""
        self.url_export: str = ""
        if json_query:
            # %todo%: read config from json-text or file
            self.init_query_elements(json_query)
        else:
            self.is_groupby: bool = False
            self.select_fields: list = []
            self.group_fields: list = []
            self.value_fields: list = []
            self.agg_functions: list = []
            self.filters: list = []

    def init_query_elements(self, json_query: str):
        self.select_fields = []
        self.filters = []

    def get_parameters(self):
        pass

    def get_user_input(self):
        def get_filters():
            st.markdown("Where clause")
            if st.button("Add filter"):
                self.filters.append(WhereExpression())

            cols = st.columns([4, 2, 4, 1])
            # if there are items in clause list
            if self.filters:
                with cols[0]:
                    st.markdown("Field")
                with cols[1]:
                    st.markdown("Operator")
                with cols[2]:
                    st.markdown("Value")
                with cols[3]:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
            id = 0
            delete_item_id = -1
            for item in self.filters:
                with cols[0]:
                    item.field = st.selectbox(
                        "Field",
                        options=self.all_fields_list,
                        label_visibility="collapsed",
                        key=f"fld{id}",
                    )
                with cols[1]:
                    item.comp = st.selectbox(
                        "Op",
                        options=COMPARE_OPERATORS,
                        label_visibility="collapsed",
                        key=f"comp{id}",
                    )
                with cols[2]:
                    item.value = st.text_input(
                        "Value", label_visibility="collapsed", key=f"val{id}"
                    )
                with cols[3]:
                    # x = st.checkbox("", key=f'cb{id}')
                    if st.button("x", key=f"cmd{id}", help="REmove this filter"):
                        delete_item_id = id
                id += 1
            if delete_item_id >= 0:
                self.filters.pop(delete_item_id)
                st.experimental_rerun()

        self.is_groupby = st.checkbox("Make group-by-query", self.is_groupby)
        if self.is_groupby:
            self.group_fields = st.multiselect(
                "Group fields",
                options=self.group_fields_options,
                default=self.group_fields,
            )
            self.value_fields = st.multiselect(
                "Value fields",
                options=self.value_fields_options,
                default=self.value_fields,
            )
            self.agg_functions = st.multiselect(
                "Aggregation funcions",
                options=SUMMARY_FUNCTIONS,
                default=self.agg_functions,
            )
            get_filters()
        else:
            self.select_fields = st.multiselect(
                "Select fields (no selection = all fields)",
                options=self.all_fields_list,
                default=self.select_fields,
            )
            get_filters()

    def build_urls(self):
        def sql_literal(value, field_name):
            _df = self.ds.fields_df
            type = _df[_df["name"] == field_name].iloc[0]["type"]
            if type in ["date", "datetime"]:
                result = f"date'{value}'"
            elif type == "text":
                result = f'"{value}"'
            else:
                result = value
            return result

        def get_where_expression():
            id = 0
            expr = ""
            for filt in self.filters:
                if id > 0:
                    expr += "%20AND%20"
                expr += (
                    f"{filt.field} {filt.comp} {sql_literal(filt.value, filt.field)}"
                )
                id += 1
            return clean_url(expr)

        def get_non_aggregation_url(url, url_count, url_export):
            if self.select_fields:
                select_fields_expr = clean_url(",".join(self.select_fields))
                url += f"&select={select_fields_expr}"
                url_export += f"&select={select_fields_expr}"
            if self.filters:
                where_expr = clean_url(get_where_expression())
                url += f"&where={where_expr}"
                url_count += f"&where={where_expr}"
                url_export += f"&where={where_expr}"
            self.url = url
            self.url_count = url_count
            self.url_export = url_export
            return url

        def get_value_fields_expression():
            lst = []
            for field in self.value_fields:
                for func in self.agg_functions:
                    lst.append(f"{func}({field}) as {func}_{field}")
            return ",".join(lst)

        def get_aggregation_url(url, url_count, url_export):
            group_fields_expr = clean_url(",".join(self.group_fields))
            value_fields_expr = clean_url(get_value_fields_expression())
            url += f"&select={group_fields_expr},{value_fields_expr}"
            url_export += f"&select={group_fields_expr},{value_fields_expr}"
            url += f"&group_by={group_fields_expr}"
            url_export += f"&group_by={group_fields_expr}"
            if self.filters:
                where_expr = clean_url(get_where_expression())
                url += f"&where={where_expr}"
                url_count += f"&where={where_expr}"
                url_export += f"&where={where_expr}"
            self.url = url
            self.url_count = url_count
            self.url_export = url_export
            return url

        url = f"{self.ds.parent.base}/api/v2/catalog/datasets/{self.ds.id}/records?limit=-1&offset={{}}&timezone=UTC"
        url_count = f"{self.ds.parent.base}/api/v2/catalog/datasets/{self.ds.id}/records?limit=1&select=count(*)"
        url_export = f"{self.ds.parent.base}/api/v2/catalog/datasets/{self.ds.id}/exports/csv/?limit=-1&timezone=UTC"
        if self.is_groupby:
            url = get_aggregation_url(url, url_count, url_export)
        else:
            url = get_non_aggregation_url(url, url_count, url_export)
        return url

    def get_match_count(self) -> int:
        """returns the number of records matched by a query without the actual data.

        Returns:
            int: number of records returned by query
        """
        response = requests.get(self.url_count)
        count = 0
        if response.status_code == 200:
            if response.json()["records"]:
                count = response.json()["records"][0]["record"]["fields"]["count(*)"]
        return count

    def get_data(self, num_of_records: int):
        """
        Retrieves data from the ODS pdata provider. Only 100 records can be retrieved per fetch command
        therefore the data is retrieved in loops with a maximum of 99 loops. if more data needs tob e fetched, the export
        option is better, as it does not use the apps memory.

        Args:
            num_of_records (int): number of records to be retrieved

        Returns:
            df (pd.DataFrame):  data as
            ok (bool):          True of data could be retrieved else False
        """
        df = None
        df_list = []
        loops = (
            num_of_records // QUERY_INCREMENT + 1
            if num_of_records < MAX_QUERY_RECORDS
            else int(MAX_QUERY_RECORDS / QUERY_INCREMENT)
        )
        for num in range(0, loops):
            response = requests.get(self.url.format(num * QUERY_INCREMENT))
            df, ok = pd.DataFrame, True
            if response.status_code == 200:
                data = response.json()["records"]
                if data:
                    df = pd.DataFrame(data)["record"]
                    df = pd.DataFrame(x["fields"] for x in df)
                    df_list.append(df)
            else:
                data = response.json()
                st.warning(
                    f"An error occurred: error_code{data['error_code']}, message: {data['message']}"
                )
                ok = False
        df = pd.concat(df_list)
        df.reset_index(drop=True, inplace=True)
        return df, ok
