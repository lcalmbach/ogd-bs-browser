import streamlit as st
import boto3
import pandas as pd
import requests
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import PROVIDERS

CATALOG_FILE = 'catalogs.json'
BUCKET_NAME = 'ods-browser-bucket'

def get_datasets(catalog):
    url = f"{catalog}/api/v2/catalog/exports/json?limit=-1&offset=0&timezone=UTC"
    # st.write(url)
    response = requests.get(url)
    ds_list = []
    if response.status_code == 200:
        data = response.json()
        ds_list = [x["dataset_id"] for x in data]
    return ds_list

def save_json_file(catalog_dict):
    with open(CATALOG_FILE, "w") as outfile:
        json.dump(catalog_dict, outfile)

def init_catalogdb_file():
    catalog_dict = {}
    for key in PROVIDERS.keys():
        catalog_dict[key] = {'datasets': get_datasets(key), 'timestamp': datetime.now().strftime("%Y-%m-%d H:M")}
    save_json_file(catalog_dict)
    
def send_mail2subscribers(catalog, new_items):
    # Define email parameters
    new_items = [f"{catalog}/explore/dataset/{x}/" for x in new_items]
    sender_email = "lukascalmbachapps@gmail.com"
    
    password = st.secrets["db_password"]
    receiver_email = "lcalmbach@gmail.com"
    
    subject = "ODS-Explorer new dataset notification"
    body = f"""Hello!\nNew datasets have been discovered for catalog {catalog}:\n{'</br>'.join(new_items)}\n\n
If you wish to unsubscribe from this service, please navigate to https://lcalmbach-ogd-bs-browser-app-as449l.streamlit.app/ 
then select the subscribe option from the menu and unselect the subscribe checkbox.\n\nHave a nice day!\nods-browser@yourService"""

    # Create a MIME message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Connect to SMTP server and send email
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender_email, password)
        smtp.send_message(message)

def open_s3_file(filename: str):
    from io import BytesIO

    session = boto3.Session()
    s3_client = session.client("s3")

    f = BytesIO()
    s3_client.download_fileobj(BUCKET_NAME, filename, f)
    data = json.loads(f.getvalue(), strict=False)
    return dict(data)

def compare_catalogs(catalog_dict):
    for catalog, item in catalog_dict.items():
        current_datasets = get_datasets(catalog)
        new_items = [x for x in current_datasets if x not in item['datasets']]
        if len(new_items) > 0:
            catalog_dict[catalog] = {'datasets': current_datasets, 'timestamp': datetime.now().strftime("%Y-%m-%d H:M")}
            send_mail2subscribers(catalog, new_items)
    save_json_file(catalog_dict)

def save_file_on_s3():
    s3 = boto3.resource('s3')
    object = s3.Object(BUCKET_NAME, 'catalogs.json')
    object.put(Body=open(CATALOG_FILE, 'rb'))

if st.button("save file"):
    data = open_s3_file('catalogs.json')
    compare_catalogs(data)