import streamlit as st
from streamlit_option_menu import option_menu

from tools import *
from ods_catalog import *
from config import *


__version__ = '0.0.1'
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2022-12-04'
MY_EMOJI = '🔭'
MY_NAME = f'ODS Data Explorer'
GIT_REPO = 'https://github.com/lcalmbach/ogd-bs-browser'

def show_info_box(catalog):
    IMPRESSUM = f"""<div style="background-color:#34282C; padding: 10px;border-radius: 15px; border:solid 1px white;">
        <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
        data from: <a href="http://data.bs.ch">OpendataSoft Data Providers</a><br>
        version: {__version__} ({VERSION_DATE})<br>
        <a href="{GIT_REPO}">git-repo</a><br>
        Current base: {catalog.base}<br>
        Current dataset: {catalog.current_dataset['id']}<br>
        """
    st.sidebar.markdown(IMPRESSUM, unsafe_allow_html=True)

def init():
    def load_css():
        with open("./style.css") as f:
            st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)
    
    st.set_page_config( 
        initial_sidebar_state = "auto", 
        page_title = MY_NAME, 
        page_icon = MY_EMOJI,
    )
    load_css()


def main():
    init()
    menu_options = ["Select Dataset", "Aggregate"]
    with st.sidebar:
        st.markdown(f"## {MY_EMOJI} {MY_NAME}")
        menu_action = option_menu(None, menu_options, 
            icons=['search', 'table', ], 
            menu_icon="cast", default_index=0)

    if menu_action == menu_options[0]:
        sel_city = st.selectbox("Data provider", list(CITIES.keys()),
            format_func=lambda x: CITIES[x])
        
        catalog = Catalog(sel_city)
        # sel_themes =  st.selectbox("🔎Themes", options=[ALL_THEMES] + catalog.themes)
        catalog.set_current_record([])
        st.session_state['catalog'] = catalog
        catalog.display_header()
    elif menu_action == menu_options[1]:
        catalog = st.session_state['catalog'] 
        catalog.show_summarized_data()
    elif menu_action == menu_options[2]:
        st.write('Export')
    show_info_box(catalog)
    

if __name__ == '__main__':
    main()

