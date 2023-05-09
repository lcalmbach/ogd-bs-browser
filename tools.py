"""
    Collection of useful functions.
"""

import random
import string
import socket
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

DEV_MACHINES = ["liestal"]
__author__ = "lcalmbach@gmail.com"

# todo
# https://www.key-shortcut.com/en/character-tables/ascii-url-encoding#:~:text=URL%20encoding%20of%20special%20characters%20The%20standard%20for,hyphen%20%22-%22%2C%20underscore%20%22_%22%2C%20dot%20%22.%22%20and%20tilde%22~%22.
# d = { 'actual character ':'replacement ',...}
# df.columns = df.columns.to_series().replace(d, regex=True)

url_enc_replacement_chars = {
    " ": "20%",
    "!": "21%",
    '"': "22%",
    "#": "23%",
    "$": "24%",
    "%": "25%",
    "&": "26%",
    "'": "27%",
    "(": "28%",
    ")": "29%",
    "*": "%2A",
    "+": "%2B",
    ",": "%2C",
    "/": "%2F",
    ":": "%3A",
    ";": "%3B",
    "=": "%3D",
    "?": "%3F",
    "@": "40%",
    "[": "%5B",
    "]": "%5D",
    "^": "%5E",
    "`": "%60",
    "<": "%3C",
    ">": "%3E",
    "@": "%40",
    "ä": "%E4",
    "ö": "%F6",
    "ü": "%FC",
    "Ä": "%C4",
    "Ö": "%D6",
    "Ü": "%DC",
}

import streamlit as st
import pandas as pd
import numpy as np
import base64
from datetime import datetime
from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode, GridUpdateMode


def get_cs_item_list(lst, separator=",", quote_string=""):
    result = ""
    for item in lst:
        result += quote_string + str(item) + quote_string + separator
    result = result[:-1]
    return result


def remove_nan_columns(df: pd.DataFrame):
    """
    Removes all empty columns from a data frame. This is used to reduce unnecessary columns when displaying tables.
    Since there is only one station table but different data collection may have different data fields, often not all
    fields are used in many cases. when displaying station or parameter information, empy columns can be excluded in
    order to make the table easier to read.

    :param df: dataframe from which empty dolumns should be removed
    :return:
    """

    lis = df.loc[:, df.isna().all()]
    for col in lis:
        del df[col]
    return df


def remove_columns(df: pd.DataFrame, lis: list) -> pd.DataFrame:
    """
    Removes columns specified in a list from a data frame. This is used to reduce unnecessary columns when
    displaying tables.

    :param lis: list of columns to remove from the dataframe
    :param df: dataframe with columns to be deleted
    :return: dataframe with deleted columns
    """

    for col in lis:
        del df[col]
    return df


def get_table_download_link(df: pd.DataFrame) -> str:
    """
    Generates a link allowing the data in a given panda dataframe to be downloaded

    :param df:  table with data
    :return:    link string including the data
    """

    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}">Downlad as csv file</a>'
    return href


def transpose_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transposes a dataframe that has exactly 1 row and n columns to a table that has 2 columns and n rows. column names
    become row headers.

    Parameters:
    -----------
    :param df:
    :return:

    :param df:  dataframe to be transposed
    :return:    transposed data frame having 2 columns and n rows
    """

    result = pd.DataFrame({"Field": [], "Value": []})
    for key, value in df.iteritems():
        df2 = pd.DataFrame({"Field": [key], "Value": [df.iloc[-1][key]]})
        result = result.append(df2)
    result = result.set_index("Field")
    return result


def dic2html_table(dic: dict, key_col_width_pct: int) -> str:
    """
    Converts a key value dictionary into a html table
    """
    html_table = "<table>"
    for x in dic:
        html_table += (
            f'<tr><td style="width: {key_col_width_pct}%;">{x}</td><td>{dic[x]}</td>'
        )
    html_table += "</table>"
    return html_table


def left(s, amount):
    return s[:amount]


def right(s, amount):
    return s[-amount:]


def mid(s, offset, amount):
    return s[offset : offset + amount]


def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)

    percentile_.__name__ = "percentile_%s" % n
    return percentile_


def add_time_columns(df):
    df["datum"] = pd.to_datetime(df["zeit"]).dt.date
    df["woche"] = df["zeit"].dt.isocalendar().week
    df["mitte_woche_datum"] = pd.to_datetime(df["zeit"]) - pd.to_timedelta(
        df["zeit"].dt.dayofweek % 7 - 2, unit="D"
    )
    df["mitte_woche_datum"] = df["mitte_woche_datum"].dt.date
    df["jahr"] = df["zeit"].dt.year
    df["monat"] = df["zeit"].dt.month
    return df


def get_table_settings(df: pd.DataFrame):
    row_height = 40
    max_height = 300

    result = {"height": 400}
    if len(df) > 0:
        height = (len(df) + 1) * row_height

        if height > max_height:
            height = max_height
        result = {"height": height}
    return result


def show_table(df: pd.DataFrame, cols=[], settings={}):
    def set_defaults():
        if "height" not in settings:
            settings["height"] = 400
        if "selection_mode" not in settings:
            settings["selection_mode"] = "single"
        if "fit_columns_on_grid_load" not in settings:
            settings["fit_columns_on_grid_load"] = True
        if "update_mode" not in settings:
            settings["update_mode"] = GridUpdateMode.SELECTION_CHANGED

    set_defaults()
    gb = GridOptionsBuilder.from_dataframe(df)
    # customize gridOptions
    gb.configure_default_column(
        groupable=False, value=True, enableRowGroup=False, aggFunc="sum", editable=False
    )
    for col in cols:
        gb.configure_column(
            col["name"],
            type=col["type"],
            precision=col["precision"],
            hide=col["hide"],
            width=col["width"],
        )
    gb.configure_selection(
        settings["selection_mode"], use_checkbox=False, rowMultiSelectWithClick=False
    )  # , suppressRowDeselection=suppressRowDeselection)
    gb.configure_grid_options(domLayout="normal")
    gridOptions = gb.build()
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        height=settings["height"],
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=settings["update_mode"],
        fit_columns_on_grid_load=settings["fit_columns_on_grid_load"],
        allow_unsafe_jscode=False,
        enable_enterprise_modules=False,
    )
    selected = grid_response["selected_rows"]
    if selected:
        return selected[0]
    else:
        return 0


def get_base64_encoded_image(image_path):
    """
    returns bytecode for an image file
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def add_time_columns(df_data):
    df = df_data
    df["datum"] = pd.to_datetime(df["zeit"]).dt.date
    df["datum"] = pd.to_datetime(df["datum"])
    df["woche"] = df_data["zeit"].dt.isocalendar().week
    df["jahr"] = df_data["zeit"].dt.year
    df["monat"] = df_data["zeit"].dt.month
    df["mitte_woche"] = pd.to_datetime(df_data["datum"]) - pd.to_timedelta(
        df["zeit"].dt.dayofweek % 7 - 2, unit="D"
    )
    df["mitte_monat"] = pd.to_datetime(df["datum"]) - pd.to_timedelta(
        df["zeit"].dt.day + 14, unit="D"
    )
    df["mitte_jahr"] = (
        df["datum"]
        - pd.to_timedelta(df["zeit"].dt.dayofyear, unit="D")
        + pd.to_timedelta(364 / 2, unit="D")
    )
    df["stunde"] = pd.to_datetime(df["zeit"]).dt.hour
    df["tag"] = df["zeit"].dt.day
    return df


def clean_url(url):
    return (
        url.replace('"', "%22")
        .replace("'", "%27")
        .replace(" ", "%20")
        .replace("<", "%3C")
        .replace(">", "%3E")
    )


def clean_url_arguments(url):
    url = clean_url(url)
    url = url.replace("=", "%3D")
    return url


def randomword(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def show_download_button(df: pd.DataFrame, cfg: dict = {}):
    if "button_text" not in cfg:
        cfg["button_text"] = "Download table"
    if "filename" not in cfg:
        cfg["filename"] = "file.csv"
    key = randomword(10)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=cfg["button_text"],
        data=csv,
        file_name=cfg["filename"],
        mime="text/csv",
        key=key,
    )


def sort_dict(dict_to_sort: dict, sort_by_col) -> dict:
    lst = sorted(dict_to_sort.items(), key=lambda x: x[sort_by_col])
    result = {x[0]: x[1] for x in lst}
    return result


def sort_object_list(lst: list, sort_field: str, reverse: bool = False) -> list:
    """
    https://www.techiedelight.com/sort-list-of-objects-python/#:~:text=A%20simple%20solution%20is%20to%20use%20the%20list.sort,accepts%20two%20optional%20keyword-only%20arguments%3A%20key%20and%20reverse.
    """
    lst.sort(key=lambda x: x[sort_field], reverse=reverse)


def send_mail(mail):
    message = MIMEMultipart()
    message["From"] = mail["sender_email"]
    message["To"] = mail["receiver_email"]
    message["Subject"] = mail["subject"]
    message.attach(MIMEText(mail["body"], "plain"))

    # Connect to SMTP server and send email
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(mail["sender_email"], mail["password"])
        smtp.send_message(message)


def get_config_value(key: str) -> str:
    if socket.gethostname().lower() in DEV_MACHINES:
        return os.environ.get(key)
    else:
        return st.secrets[key]
