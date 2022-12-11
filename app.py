import streamlit as st
from streamlit_option_menu import option_menu

from tools import *
from ods_catalog import *
from config import *


__version__ = '0.0.4'
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2022-12-11'
MY_EMOJI = '🔭'
MY_NAME = f'ODS Data Explorer'
GIT_REPO = 'https://github.com/lcalmbach/ogd-bs-browser'
APP_URL = 'https://lcalmbach-ogd-bs-browser-app-as449l.streamlit.app/'

def show_info_box(catalog):
    IMPRESSUM = f"""<div style="background-color:#34282C; padding: 10px;border-radius: 15px; border:solid 1px white;">
        <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
        data from: Various OpendataSoft Data Providers<br>
        version: {__version__} ({VERSION_DATE})<br>
        <a href="{GIT_REPO}">git-repo</a><br>
        Current provider: {PROVIDERS[catalog.base]}<br>
        Current dataset: {catalog.current_dataset.id}<br>
        """
    st.sidebar.markdown(IMPRESSUM, unsafe_allow_html=True)


def init_layout():
    def load_css():
        with open("./style.css") as f:
            st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)
    
    st.set_page_config( 
        initial_sidebar_state = "auto", 
        page_title = MY_NAME, 
        page_icon = MY_EMOJI,
    )
    load_css()

def init_settings():
    if 'provider' not in st.session_state:
        st.session_state['provider'] = list(PROVIDERS.keys())[0]
        st.session_state['catalog'] = Catalog(st.session_state['provider']) 

def main():
    init_layout()
    init_settings()
    menu_options = ["Select Dataset", "Query"]
    with st.sidebar:
        st.markdown(f"## {MY_EMOJI} {MY_NAME}")
        # https://fonts.google.com/icons
        menu_action = option_menu(None, menu_options, 
            icons=['search', 'table', 'download'], 
            menu_icon="cast", default_index=0)

    if menu_action == menu_options[0]:
        index = list(PROVIDERS.keys()).index(st.session_state['provider'])
        sel_provider = st.selectbox("Data provider",
            list(PROVIDERS.keys()), 
            format_func=lambda x: PROVIDERS[x],
            index=index
        )
        if st.session_state['provider'] == sel_provider:
            catalog = st.session_state['catalog']
        else:
            catalog = Catalog(sel_provider) 
            st.session_state['provider'] = sel_provider
            st.write(st.session_state['provider'])
        catalog.set_current_record()
        st.session_state['catalog'] = catalog
        catalog.current_dataset.display_header()
    elif menu_action == menu_options[1]:
        catalog = st.session_state['catalog'] 
        catalog.current_dataset.display_query_result()
    show_info_box(catalog)
    

if __name__ == '__main__':
    main()

