import os
import time
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

if st.session_state['authentication_status']:
    # Cache data
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

        # Button to refresh
        if st.button("Refresh"):
            # Clear cache
            # st.cache_data.clear()
            # Reload page
            st.rerun()
        
        # Get accounts from API flask
        with st.spinner("Loading accounts..."):
            accounts = get_accounts()
        
        if len(accounts) == 0:
            st.warning("No accounts found.")
            st.stop()
        
        # Load to dataframe
        df = pd.DataFrame(accounts, columns=[
            "id",
            "name",
            "email",
            "status",

            "month_before_banned",
            "max_of_apps",
            "max_vector_space",
            "max_annotation_quota_limit",
            "max_documents_upload_quota",

            "last_login_at",
            "last_login_ip",
            "last_active_at",
            "created_at",
            "updated_at"
        ])
        
        df = df.sort_values(by=['created_at'])

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
                "month_before_banned": st.column_config.NumberColumn(
                    "month_before_banned",
                    help="The number of months before the user account is banned",
                    required=True,
                ),
                "max_of_apps": st.column_config.NumberColumn(
                    "max_of_apps",
                    help="The maximum number of apps that a user can create",
                    required=True,
                ),
                "max_vector_space": st.column_config.NumberColumn(
                    "max_vector_space",
                    help="The maximum size vector spaces (MB)",
                    required=True,
                ),
                "max_annotation_quota_limit": st.column_config.NumberColumn(
                    "max_annotation_quota_limit",
                    help="The maximum number of annotation quota limit that a user can create",
                    required=True,
                ),
                "max_documents_upload_quota": st.column_config.NumberColumn(
                    "max_documents_upload_quota",
                    help="The maximum number of documents upload quota that a user can create",
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
        edited_df = edited_df.to_dict(orient="records")
        # Check if there are changes
        if df.to_dict(orient="records") == edited_df:
            # st.info("No changes detected.")
            pass
        else:
            res = requests.put(f"{api_url}/accounts", json=edited_df)

            if res.status_code == 200:
                st.success("Changes saved successfully.")
                # Clear cache
                # st.cache_data.clear()
                # Reload page
                st.rerun()
            else:
                st.error("Failed to save changes.")
                time.sleep(2)
                st.rerun()

        # Delete account by ID, UI form for input ID to delete
        st.markdown("### Delete Account")
        with st.form("delete_account_form"):
            delete_id = st.text_input("Enter Account ID to delete")
            submit_button = st.form_submit_button("Delete Account")
        
        if submit_button:
            if delete_id:
                try:
                    st.write(f"{api_url}/accounts/{delete_id}")
                    res = requests.delete(f"{api_url}/accounts/{delete_id}")
                    try:
                        resjson = res.json()
                        if resjson['status'] == "success":
                            st.success(f"Account {delete_id} deleted successfully.")
                            st.rerun()
                        else:
                            st.error(f"Error: {resjson['message']}")
                    except:
                        st.error(f"Unknow error: {res.text}")
                except Exception as e:
                    st.error(f"Error request: {e}")
            else:
                st.error("Please enter a valid Account ID.")

else:
    st.warning("Please log in to access the dashboard.")