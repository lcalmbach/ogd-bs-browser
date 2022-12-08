import streamlit as st
import requests
import pandas as pd
import io
import locale

from tools import *
from text import *
from config import *

locale.setlocale(locale.LC_ALL, '')

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


    def record_count(self):
        url = f"{self.base}/api/v2/catalog/datasets/{self.current_dataset['id']}/records?limit=1&offset=0&timezone=UTC"
        response = requests.get(url)
        count = 0
        if response.status_code == 200:
            data = response.json()
            count = data["total_count"]
        return count


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
        df = pd.DataFrame()
        if response.status_code == 200:
            data = response.json()
            if 'dcat' in data[0]['metas']:
                df = [{'id': x['dataset_id'], 
                    'fields': x['fields'], 
                    'title': x['metas']['default']['title'],
                    'description': x['metas']['default']['description'],
                    'themes': x['metas']['default']['theme'],
                    'issued': x['metas']['dcat']['issued'],
                    } for x in data]
            else:
                df = [{'id': x['dataset_id'], 
                    'fields': x['fields'], 
                    'title': x['metas']['default']['title'],
                    'description': x['metas']['default']['description'],
                    'themes': x['metas']['default']['theme'],
                    'issued': None,
                    } for x in data]

            df = pd.DataFrame(df)
        df['issued'] = pd.to_datetime(df['issued'], errors='coerce')
        return df

    
    def set_current_record(self, themes):
        def filter_for_title(find_expression):
            df = self.datasets
            df = df[df['title'].str.contains(find_expression)]
            return df

        def filter_for_themes(df, themes_filter):
            _df = self.dataset_theme[self.dataset_theme['theme'].isin(themes_filter)]
            df = _df.set_index('dataset_id').join(df.set_index('id'), how='inner')
            df = df.reset_index()
            df = df.rename(columns={'index':'id'})
            df = df.drop('theme', axis=1)
            df.drop_duplicates(subset='id')
            return df
        
        def filter_for_dates(df, days):
            df['x'] =  pd.to_datetime("today") - pd.to_timedelta(f"{days} day")
            _df = df[ df['issued'] > df['x']]
            return _df

        with st.expander('🔎Filter Datasets', expanded=True):
            cols = st.columns(3)
            with cols[0]:
                title_filter = st.text_input('Title contains:')
            with cols[1]:
                themes_filter = st.multiselect('Dataset belongs to theme(s):', self.all_themes)
            with cols[2]:
                date_filter = st.number_input('Issued during last n days:',min_value=0,max_value=10000)
        df = self.datasets if title_filter == '' else filter_for_title(title_filter)
        if len(themes_filter) > 0:
            df = filter_for_themes(df, themes_filter)
        if date_filter > 0:
            df = filter_for_dates(df, date_filter)
        settings = get_table_settings(df)

        st.markdown('### Datasets')
        st.write(f"{len(df)} records")
        cols = [{'name': 'id', 'type': 'str', 'hide': False, 'precision': 0, 'width':100}, 
            {'name': 'issued', 'hide': False, 'precision': 0, 'type': 'date', 'width':100},
            {'name': 'title', 'hide': False, 'precision': 0, 'type': 'str', 'width':500},
            ]
        response = show_table(df[['id', 'title', 'issued']], cols, settings)
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
            self.preview_data(100)
        with tabs[1]:
            self.show_fields()


    def preview_data(self, rows):
        url = f"{self.base}/api/v2/catalog/datasets/{self.current_dataset['id']}/exports/csv/?limit={rows}&offset=0&timezone=UTC"
        response = requests.get(url)
        df = pd.read_csv(io.StringIO(response.text), sep=";")
        record_count = len(df) if len(df) < rows else self.record_count() 
        st.write(f"{record_count :n} records")
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
    
    
    def show_export(self):
        def get_select_url(select_fields, filter):
            
            url = f"{self.base}/api/v2/catalog/datasets/{self.current_dataset['id']}/exports/csv/?limit=-1&timezone=UTC"
            if select_fields:
                select_fields_expr = ','.join(select_fields)
                url += f"&select={select_fields_expr}"
            if filter:
                #filter_expr = ','.join(filter)
                url += f"&where={filter}"
            # url = f"https://data.bs.ch/explore/dataset/{self.current_dataset['id']}/download/?format=csv&timezone=Europe/Berlin&lang=de&csv_separator=%3B&select={select_fields_expr}"
            url = clean_url(url)
            return url

        st.write(f"**Export dataset: {self.current_dataset['title']}**")
        with st.sidebar.expander("⚙️ Select:", expanded=True):
            sel_select_fields = st.multiselect("Fields", self.fields)
        with st.sidebar.expander("⚙️ Filter:", expanded=True):
            cols = st.columns([2,1,2])
            """with cols[0]:
                sel_field = st.selectbox("Fields", self.fields)
            with cols[1]:
                sel_op = st.selectbox("", ['like','=','<','>'])
            with cols[2]:
                sel_value = st.text_input("Value")
            sel_filters = clean_url(f"{sel_field} {sel_op} {sel_value}")"""
            sel_filters = clean_url_arguments(st.text_area("Filter"))
        url = get_select_url(sel_select_fields, sel_filters)
        st.write(url)
        st.write('Click Link to download')