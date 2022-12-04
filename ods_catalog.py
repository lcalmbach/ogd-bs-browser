import streamlit as st
import requests
import pandas as pd
import io

from tools import *
from text import *
from config import *

class Catalog():
    def __init__(self, base):
        self.base = base
        self.datasets = self.get_datasets()
        self.current_dataset = {}
        self.fields = []
        self.all_themes, self.dataset_theme = self.get_themes()


    def show_fields(self):
        df = pd.DataFrame({'name':[], 'description': [], 'label': [], 'type': []})
        for item in self.current_dataset['fields']:
            df.loc[len(df.index)] = [item['name'], item['description'], item['label'], item['type']]
        cols = []
        settings = get_table_settings(df)
        response = show_table(df, cols, settings)

    def get_themes(self):
        themes = []
        dataset_theme = pd.DataFrame({'dataset_id': [], 'theme':[]})
        for index, row in self.datasets.iterrows():
            if row['themes']:
                for item in row['themes']:
                    themes.append(item)
                    df = pd.DataFrame({'dataset_id': [row['id']], 'theme':[item]})
                    dataset_theme = pd.concat([dataset_theme, df])
        themes = list(set(themes))
        themes.sort()
        return themes, dataset_theme

    def get_datasets(self):
        url = f"{self.base}/api/v2/catalog/exports/json?limit=-1&offset=0&timezone=UTC"
        response = requests.get(url)
        x = pd.DataFrame()
        if response.status_code == 200:
            data = response.json()
            x = [{'id': x['dataset_id'], 
                'fields': x['fields'], 
                'title': x['metas']['default']['title'],
                'description': x['metas']['default']['description'],
                'themes': x['metas']['default']['theme']
                } for x in data]
            x = pd.DataFrame(x)
        return  x


    def get_datasets1(self):
        offset=0
        ok=True
        results = []
        while ok:
            url = f"{self.base}/api/v2/catalog/datasets?limit=100&offset={offset}&timezone=UTC"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()['datasets']
                ok = len(data) > 0
                if ok:
                    # st.write(data)
                    x = [{'id': x['dataset']['dataset_id'], 
                        'fields': x['dataset']['fields'], 
                        'title': x['dataset']['metas']['default']['title'],
                        'description': x['dataset']['metas']['default']['description'],
                        'themes': x['dataset']['metas']['default']['theme']
                        } for x in data]
                    results.append(pd.DataFrame(x))
                offset += 100
        return  pd.concat(results)
    
    def get_filtered_datasets(self, find_expression):
        """search forf theme: for index, item in self.datasets.iterrow():
            if theme.isin(item['themes']):
                st.write(item)"""
        df = self.datasets
        df = df[df['title'].str.contains(find_expression)]
        return df


    def set_current_record(self, themes):
        def filter_for_themes(df, themes_filter):
            _df = self.dataset_theme[self.dataset_theme['theme'].isin(themes_filter)]
            df = _df.set_index('dataset_id').join(df.set_index('id'), how='inner')
            df = df.reset_index()
            df = df.rename(columns={'index':'id'})
            df = df.drop('theme', axis=1)
            df.drop_duplicates(subset='id')
            return df

        cols = st.columns(2)
        with cols[0]:
            title_filter = st.text_input('Title contains:')
        with cols[1]:
            themes_filter = st.multiselect('Dataset belongs to theme(s):', self.all_themes)
        df = self.datasets if title_filter == '' else self.get_filtered_datasets(title_filter)
        if len(themes_filter) > 0:
            df = filter_for_themes(df, themes_filter)
        settings = get_table_settings(df)

        st.markdown('### Datasets')
        st.write(f"{len(df)} records")
        cols = [{'name': 'id', 'type': 'str', 'hide': False, 'precision': 0, 'width':100}, 
            {'name': 'title', 'hide': False, 'precision': 0, 'type': 'str', 'width':500}]
        response = show_table(df[['id', 'title']], cols, settings)
        if response:
            self.current_dataset = self.datasets[self.datasets["id"]==response['id']].iloc[0]
            self.fields = [x['name'] for x in self.current_dataset['fields']]
        else:
            self.current_dataset = self.datasets.iloc[0]


    def display_header(self):
        st.markdown(f"### {self.current_dataset['title']}")
        st.markdown(self.current_dataset['description'], unsafe_allow_html=True)
        link = f"{self.base}/explore/dataset/{self.current_dataset['id']}/table"
        st.markdown(f"[Open record at data provider]({link})")
        tabs = st.tabs(['Preview', 'Fields'])
        with tabs[0]:
            self.export_data(100)
        with tabs[1]:
            self.show_fields()


    def export_data(self, rows):
        url = f"{self.base}/api/v2/catalog/datasets/{self.current_dataset['id']}/exports/csv/?limit={rows}&offset=0&timezone=UTC"
        response = requests.get(url)
        df = pd.read_csv(io.StringIO(response.text), sep=";")
        st.write(f"{len(df)} records")
        st.write(df)


    def get_summary_data(self, group_fields, value_fields, func, sel_filters):
        group_fields_expr = ", ".join(group_fields)
        value_fields = [f"{func}({x}) as {func}_{x}" for x in value_fields]
        value_fields_expr = ", ".join(value_fields)
        url = f"{self.base}/api/v2/catalog/datasets/{self.current_dataset['id']}/records?limit=-1&offset=0&timezone=UTC&select={group_fields_expr},{value_fields_expr}&group_by={group_fields_expr}"
        if sel_filters:
            url += f"&where={sel_filters}"
        response = requests.get(url)
        df, ok = pd.DataFrame, True
        if response.status_code == 200:
            data = response.json()['records']
            df = pd.DataFrame(data)['record']
            df = pd.DataFrame(x['fields'] for x in df)
        else:
            data = response.json()
            st.warning(f"An error occurred: error_code{data['error_code']}, message: {data['message']}")
            ok = False
        with st.expander('URL'):
            st.markdown(f"```{url}```")
        return df, ok


    def show_summarized_data(self):
        st.write(f"**Summary report for dataset: {self.current_dataset['title']}**")
        with st.sidebar.expander("⚙️ Group by:", expanded=True):
            sel_group_fields = st.multiselect("Group fields", self.fields)
            sel_value_field = st.multiselect("Value fields", self.fields)
            sel_agg_func = st.selectbox("Summary function", SUMMARY_FUNCTIONS)
        with st.sidebar.expander("⚙️ Filter:", expanded=True):
            sel_filters = st.text_area("filters")
        if st.button("get data"):
            df, ok = self.get_summary_data(sel_group_fields,sel_value_field,sel_agg_func, sel_filters)
            if ok:
                st.write(df)
                #st.markdown(get_table_download_link(df), unsafe_allow_html=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Press to Download",
                    csv,
                    "file.csv",
                    "text/csv",
                    key='download-csv'
                )