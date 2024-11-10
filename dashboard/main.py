import os
import pandas as pd
import requests
import streamlit as st
import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader

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

try:
    authenticator.login()
except Exception as e:
    st.error(e)

st.title("Dify Dashboard by Hotamago")

# Cache data
@st.cache_data
def get_accounts():
    res = requests.get(f"{api_url}/accounts")
    if res.status_code == 200:
        return res.json()
    else:
        raise Exception("Failed to load accounts.")

# Sidebar
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Accounts"])

if menu == "Accounts":
    st.subheader("Accounts")
    
    # Get accounts from API flask
    with st.spinner("Loading accounts..."):
        accounts = get_accounts()
    
    # Load to dataframe
    df = pd.DataFrame(
        accounts,
        columns=[
            "id",
            "name",
            "email",
            "status",
            "last_login_at",
            "last_login_ip",
            "last_active_at",
            "created_at",
            "updated_at"
        ])

    # Show accounts
    edited_df = st.data_editor(
        df,
        column_config={
            "status": st.column_config.SelectboxColumn(
                "status",
                help="Account status",
                options=["pending", "uninitialized", "active", "banned", "closed"],
                required=True,
            ),
        },
        disabled=[
            "id",
            "name",
            "email",
            "last_login_at",
            "last_login_ip",
            "last_active_at",
            "created_at",
            "updated_at"
        ], # diable all columns
        hide_index=True,
    )

    # Save changes
    if st.button("Save changes"):
        edited_df = edited_df.to_dict(orient="records")
        res = requests.post(f"{api_url}/accounts", json=edited_df)

        if res.status_code == 200:
            st.success("Changes saved successfully.")
            # Clear cache
            st.cache_data.clear()
        else:
            st.error("Failed to save changes.")
    
    # Reload data
    if st.button("Reload data"):
        st.cache_data.clear()
        st.rerun()