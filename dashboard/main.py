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

    # Add functions for Plans API
    def get_plans():
        res = requests.get(f"{api_url}/plans")
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Failed to load plans: {res.status_code} {res.text}")
            return []

    def update_plans(plans_data):
        res = requests.put(f"{api_url}/plans", json=plans_data)
        return res

    # Sidebar
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("Go to", ["Accounts", "Plans"])

    if menu == "Accounts":
        st.subheader("Accounts")

        # Button to refresh
        if st.button("Refresh"):
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

            "id_custom_plan",
            "plan_expiration",
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

        # Convert plan_expiration strings to datetime for editing
        df['plan_expiration'] = pd.to_datetime(df['plan_expiration'])

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
                "id_custom_plan": st.column_config.TextColumn(  # replaced StringColumn -> TextColumn
                    "id_custom_plan",
                    help="The ID of the custom plan",
                    required=True,
                ),
                "plan_expiration": st.column_config.DatetimeColumn(
                    "plan_expiration",
                    help="The date when the plan expires",
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
            ],
            hide_index=True,
        )

        # Save changes
        edited_df = edited_df.to_dict(orient="records")
        if df.to_dict(orient="records") == edited_df:
            pass
        else:
            res = requests.put(f"{api_url}/accounts", json=edited_df)

            if res.status_code == 200:
                st.success("Changes saved successfully.")
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

    elif menu == "Plans":
        st.subheader("Manage Plans")

        # Button to refresh
        if st.button("Refresh Plans"):
            st.rerun()

        # Get plans from API
        with st.spinner("Loading plans..."):
            plans_data = get_plans()

        if 'plans_df' not in st.session_state or st.session_state.plans_data != plans_data:
            st.session_state.plans_data = plans_data
            # Convert nested features dict to separate columns for editing
            flat_plans = []
            for plan in plans_data:
                flat_plan = plan.copy()
                features = flat_plan.pop('features', {})
                flat_plan.update(features)
                flat_plans.append(flat_plan)
            st.session_state.plans_df = pd.DataFrame(flat_plans)
            # Ensure plan_expiration is integer days
            if 'plan_expiration' in st.session_state.plans_df.columns:
                st.session_state.plans_df['plan_expiration'] = st.session_state.plans_df['plan_expiration'].astype(int)


        if st.session_state.plans_df.empty:
            st.warning("No plans found or failed to load.")
            # Optionally allow creating the first plan
            if st.button("Add First Plan"):
                 # Add a default row to the DataFrame in session state
                default_features = {
                    "members": 1,
                    "apps": 10,
                    "vector_space": 100,
                    "knowledge_rate_limit": 10,
                    "annotation_quota_limit": 100,
                    "documents_upload_quota": 50
                }
                new_plan_row = pd.DataFrame([{
                    "id": str(uuid.uuid4()),
                    "name": "New Plan",
                    "description": "Default description",
                    "price": 0.0,
                    "plan_expiration": 30,  # default days
                    **default_features
                }])
                st.session_state.plans_df = pd.concat([st.session_state.plans_df, new_plan_row], ignore_index=True)
                st.rerun()

        else:
            st.info("Edit plan details below. Click 'Add New Plan' to add a row, then 'Save Changes' to update all plans.")

            edited_plans_df = st.data_editor(
                st.session_state.plans_df,
                column_config={
                    "id": st.column_config.TextColumn("ID (read-only)", disabled=True),
                    "name": st.column_config.TextColumn("Name", required=True),
                    "description": st.column_config.TextColumn("Description"),
                    "price": st.column_config.NumberColumn("Price", format="%.2f", required=True),
                    "plan_expiration": st.column_config.NumberColumn(
                        "Expiration Days",
                        help="Number of days until expiration",
                        required=True,
                        min_value=0
                    ),
                    "members": st.column_config.NumberColumn("Members Limit", required=True, min_value=1),
                    "apps": st.column_config.NumberColumn("Apps Limit", required=True, min_value=0),
                    "vector_space": st.column_config.NumberColumn("Vector Space (MB)", required=True, min_value=0),
                    "knowledge_rate_limit": st.column_config.NumberColumn("Knowledge Rate Limit", required=True, min_value=0),
                    "annotation_quota_limit": st.column_config.NumberColumn("Annotation Quota Limit", required=True, min_value=0),
                    "documents_upload_quota": st.column_config.NumberColumn("Docs Upload Quota", required=True, min_value=0),
                },
                hide_index=True,
                num_rows="dynamic",
                
                key="plan_editor"
            )

            # Check if changes were made
            original_df_dict = st.session_state.plans_df.to_dict(orient="records")
            edited_df_dict = edited_plans_df.to_dict(orient="records")

            col1, col2 = st.columns(2)
            with col1:
                 # Button to add a new plan row to the editor
                if st.button("Add New Plan Row"):
                    default_features = {
                        "members": 1,
                        "apps": 10,
                        "vector_space": 100,
                        "knowledge_rate_limit": 10,
                        "annotation_quota_limit": 100,
                        "documents_upload_quota": 50
                    }
                    new_id = str(uuid.uuid4())
                    # Add to the DataFrame being edited
                    new_plan_row = pd.DataFrame([{
                        "id": new_id,
                        "name": "New Plan",
                        "description": "Enter description",
                        "price": 0.0,
                        "plan_expiration": 30,  # default days
                        **default_features
                    }])
                    # Update the session state DataFrame directly for the editor
                    st.session_state.plans_df = pd.concat([edited_plans_df, new_plan_row], ignore_index=True)
                    st.rerun()

            with col2:
                # Save changes button (only active if changes detected)
                save_disabled = original_df_dict == edited_df_dict
                if st.button("Save Changes", disabled=save_disabled):
                    # Reconstruct the nested structure expected by the API
                    plans_to_save = []
                    for _, row in edited_plans_df.iterrows():
                        plan_dict = row.to_dict()
                        features = {
                            "members": int(plan_dict.pop("members")),
                            "apps": int(plan_dict.pop("apps")),
                            "vector_space": int(plan_dict.pop("vector_space")),
                            "knowledge_rate_limit": int(plan_dict.pop("knowledge_rate_limit")),
                            "annotation_quota_limit": int(plan_dict.pop("annotation_quota_limit")),
                            "documents_upload_quota": int(plan_dict.pop("documents_upload_quota"))
                        }
                        # Number of days until expiration
                        plan_dict['plan_expiration'] = int(plan_dict['plan_expiration'])
                        plan_dict['features'] = features
                        # Ensure price is float
                        plan_dict['price'] = float(plan_dict['price'])
                        plans_to_save.append(plan_dict)

                    res = update_plans(plans_to_save)

                    if res.status_code == 200:
                        st.success("Plans updated successfully.")
                        # Update session state with the saved data and rerun
                        st.session_state.plans_data = plans_to_save
                        st.session_state.plans_df = edited_plans_df
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to save plans: {res.status_code} {res.text}")
                        time.sleep(2)

else:
    st.warning("Please log in to access the dashboard.")