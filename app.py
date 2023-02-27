import streamlit as st
from streamlit_option_menu import option_menu
import requests
import json

from tools import *
from ods_catalog import *
from config import *


__version__ = "0.1.1"
__author__ = "Lukas Calmbach"
__author_email__ = "lcalmbach@gmail.com"
VERSION_DATE = "2023-27-02"
MY_EMOJI = "🔭"
MY_NAME = f"ODS Data Explorer"
GIT_REPO = "https://github.com/lcalmbach/ogd-bs-browser"
APP_URL = "https://lcalmbach-ogd-bs-browser-app-as449l.streamlit.app/"


def get_providers()->dict:
    response = requests.get(PROVIDERS_URL)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error: Failed to retrieve catalog data from the URL.")
    

def show_info_box():
    catalog = st.session_state["catalog"]
    ds_link = f"{catalog.base}/explore/dataset/{catalog.current_dataset.id}"
    text = f"""Current provider: [{st.session_state["providers_dict"][catalog.base]}]({catalog.base})<br>
        Current dataset: [{catalog.current_dataset.id}]({ds_link})<br><br>"""
    st.sidebar.markdown(text, unsafe_allow_html=True)
    impressum = f"""<div style="background-color:#34282C; padding: 10px;border-radius: 15px; border:solid 1px white;">
        <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
        data from: Various OpendataSoft Data Providers<br>
        version: {__version__} ({VERSION_DATE})<br>
        <a href="{GIT_REPO}">git-repo</a><br>
        """
    st.sidebar.markdown(impressum, unsafe_allow_html=True)


def init_layout():
    def load_css():
        with open("./style.css") as f:
            st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

    st.set_page_config(
        initial_sidebar_state="auto",
        page_title=MY_NAME,
        page_icon=MY_EMOJI,
    )
    load_css()


def init_settings():
    if "provider" not in st.session_state:
        st.session_state["provider"] = DEFAULT_PROVIDER
        st.session_state["providers_dict"] = get_providers()
        st.session_state["catalog"] = Catalog(st.session_state["provider"])
        st.session_state["email_address"] = ''
        
        


def main():
    init_layout()
    init_settings()
    menu_options = ["Select Dataset", "Query", "Subscriptions", "About"]
    with st.sidebar:
        st.markdown(f"## {MY_EMOJI} {MY_NAME}")
        # https://fonts.google.com/icons
        menu_action = option_menu(
            None,
            menu_options,
            icons=["search", "table", "info"],
            menu_icon="cast",
            default_index=0,
        )

    if menu_action == menu_options[0]:
        provider_options = sort_dict(st.session_state["providers_dict"], 1)
        index = list(provider_options.keys()).index(st.session_state["provider"])
        sel_provider = st.selectbox(
            "Select a data provider (catalog)",
            options=list(provider_options.keys()),
            format_func=lambda x: provider_options[x],
            index=index,
        )
        if st.session_state["provider"] == sel_provider:
            catalog = st.session_state["catalog"]
        else:
            catalog = Catalog(sel_provider)
            st.session_state["provider"] = sel_provider
            st.write(st.session_state["provider"])
        catalog.set_current_record()
        st.session_state["catalog"] = catalog
        catalog.current_dataset.display_header()
    elif menu_action == menu_options[1]:
        catalog = st.session_state["catalog"]
        catalog.current_dataset.display_query_result()
    elif menu_action == menu_options[2]:
        catalog = st.session_state["catalog"]
        catalog.subscribe()
    elif menu_action == menu_options[3]:
        catalog = st.session_state["catalog"]
        catalog.display_info_page()
    show_info_box()


if __name__ == "__main__":
    main()
