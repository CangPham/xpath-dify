import os
import time
import pandas as pd
import requests
import streamlit as st
import streamlit_authenticator as stauth
import uuid
from yaml.loader import SafeLoader

import yaml

with open("./config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Using environment variables or config file
api_url = (os.getenv("API_URL") if os.getenv("API_URL") else config['api']['url']) + "/dashboard"
# print(f"API URL: {api_url}")

st.set_page_config(page_title="Dashboard", page_icon=":bar_chart:", layout="wide")

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Load components
from components.accounts import render as render_accounts
from components.plans import render as render_plans
from components.payments import render as render_payments

try:
    authenticator.login()
except Exception as e:
    st.error(e)

if st.session_state['authentication_status']:
    # Sidebar
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("Go to", ["Accounts", "Plans", "Payments"])

    if menu == "Accounts":
        render_accounts(config, api_url)

    elif menu == "Plans":
        render_plans(config, api_url)

    elif menu == "Payments":
        render_payments(config, api_url)

else:
    st.warning("Please log in to access the dashboard.")