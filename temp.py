def init():
    if 'sel_provider' not in st.session_state:
        st.session_state['sel_provider']=CITIES[0]
        st.session_state['catalog'] = Catalog(st.session_state['sel_provider']) 

def get_summary_data(self, group_fields, value_fields, func, sel_filters):
        group_fields_expr = clean_url(", ".join(group_fields))
        value_fields = [f"{func}({x}) as {func}_{x}" for x in value_fields]
        value_fields_expr = clean_url(", ".join(value_fields))
        url = f"{self.base}/api/v2/catalog/datasets/{self.current_dataset.id}/records?limit=-1&offset=0&timezone=UTC&select={group_fields_expr},{value_fields_expr}&group_by={group_fields_expr}"
        if sel_filters:
            url += f"&where={clean_url(sel_filters)}"
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


    def show_export(self):
        def get_select_url(select_fields, filter):
            url = f"{self.base}/api/v2/catalog/datasets/{self.current_dataset.id}/exports/csv/?limit=-1&timezone=UTC"
            if select_fields:
                select_fields_expr = ','.join(select_fields)
                url += f"&select={select_fields_expr}"
            if filter:
                #filter_expr = ','.join(filter)
                url += f"&where={filter}"
            # url = f"https://data.bs.ch/explore/dataset/{self.current_dataset.id}/download/?format=csv&timezone=Europe/Berlin&lang=de&csv_separator=%3B&select={select_fields_expr}"
            url = clean_url(url)
            return url
        
            
        st.write(f"**Export dataset: {self.current_dataset.title}**")
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
        if st.button('⬇️ Download'):
            webbrowser.open_new_tab(url)
