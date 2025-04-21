import os
import time
import pandas as pd
import requests
import streamlit as st
import streamlit_authenticator as stauth
import uuid

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

    # Add functions for Plans API
    def get_plans():
        res = requests.get(f"{api_url}/plans")
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Failed to load plans: {res.status_code} {res.text}")
            return []

    def add_plan(plan_data):
        res = requests.post(f"{api_url}/plans", json=plan_data)
        return res

    def update_plans(plans_data):
        res = requests.put(f"{api_url}/plans", json=plans_data)
        return res

    def delete_plan(plan_id):
        res = requests.delete(f"{api_url}/plans/{plan_id}")
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
                "id_custom_plan": st.column_config.StringColumn(
                    "id_custom_plan",
                    help="The ID of the custom plan",
                    required=True,
                ),
                "plan_expiration": st.column_config.DateInputColumn(
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
            plans = get_plans()

        if not plans:
            st.warning("No plans found or failed to load.")
        
        # Define expected columns, including 'order' for arrangement
        plan_columns = [
            "id",
            "name",
            "price",
            "features",
            "order",
            "is_active",
            "created_at",
            "updated_at"
        ]
        
        # Load to dataframe, ensuring all columns exist, filling missing with defaults if necessary
        df_plans = pd.DataFrame(plans)
        for col in plan_columns:
            if col not in df_plans.columns:
                if col == 'order':
                    df_plans[col] = 0
                elif col == 'is_active':
                    df_plans[col] = True
                elif col in ['price']:
                    df_plans[col] = 0.0
                else:
                    df_plans[col] = None

        # Reorder columns for display
        df_plans = df_plans[plan_columns]

        # Sort by 'order' column for display
        df_plans = df_plans.sort_values(by=['order', 'created_at'])

        st.markdown("### Edit Plans")
        edited_df_plans = st.data_editor(
            df_plans,
            column_config={
                "id": st.column_config.TextColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("Name", required=True),
                "price": st.column_config.NumberColumn("Price", format="$%.2f", required=True),
                "features": st.column_config.TextColumn("Features (comma-separated)", required=False),
                "order": st.column_config.NumberColumn("Order", help="Position in list (lower numbers first)", required=True, step=1),
                "is_active": st.column_config.CheckboxColumn("Active?", required=True),
                "created_at": st.column_config.DatetimeColumn("Created", disabled=True, format="YYYY-MM-DD HH:mm:ss"),
                "updated_at": st.column_config.DatetimeColumn("Updated", disabled=True, format="YYYY-MM-DD HH:mm:ss"),
            },
            disabled=[
                "id",
                "created_at",
                "updated_at"
            ],
            hide_index=True,
            num_rows="dynamic",
        )

        # Save changes (Edits and Reordering via PUT)
        edited_plans_list = edited_df_plans.to_dict(orient="records")

        if df_plans.to_dict(orient="records") != edited_plans_list:
            if st.button("Save Plan Changes"):
                with st.spinner("Saving plan changes..."):
                    for plan in edited_plans_list:
                        if 'price' in plan and plan['price'] is not None:
                            try:
                                plan['price'] = float(plan['price'])
                            except (ValueError, TypeError):
                                st.error(f"Invalid price format for plan {plan.get('name', plan.get('id'))}")
                                st.stop()
                        if 'order' in plan and plan['order'] is not None:
                            try:
                                plan['order'] = int(plan['order'])
                            except (ValueError, TypeError):
                                st.error(f"Invalid order format for plan {plan.get('name', plan.get('id'))}")
                                st.stop()

                    res = update_plans(edited_plans_list)
                    if res.status_code == 200:
                        st.success("Plan changes saved successfully.")
                        st.rerun()
                    else:
                        st.error(f"Failed to save plan changes: {res.status_code} {res.text}")
                        time.sleep(2)

        # Add New Plan Form
        st.markdown("### Add New Plan")
        with st.form("add_plan_form", clear_on_submit=True):
            new_name = st.text_input("Plan Name", key="add_name")
            new_price = st.number_input("Price", min_value=0.0, format="%.2f", key="add_price")
            new_features = st.text_area("Features (comma-separated)", key="add_features")
            new_order = st.number_input("Order", min_value=0, step=1, value=(max(df_plans['order']) + 10) if not df_plans.empty else 0, key="add_order")
            new_is_active = st.checkbox("Is Active?", value=True, key="add_active")
            add_submit_button = st.form_submit_button("Add Plan")

            if add_submit_button:
                if new_name:
                    new_plan_data = {
                        "name": new_name,
                        "price": new_price,
                        "features": new_features,
                        "order": new_order,
                        "is_active": new_is_active
                    }
                    with st.spinner("Adding new plan..."):
                        res = add_plan(new_plan_data)
                        try:
                            res_data = res.json()
                            if res.status_code == 200 or res.status_code == 201:
                                st.success(f"Plan '{new_name}' added successfully.")
                                st.rerun()
                            else:
                                st.error(f"Error adding plan: {res_data.get('message', res.text)}")
                        except Exception as e:
                            st.error(f"Failed to process response: {res.text} | Error: {e}")
                else:
                    st.error("Plan Name is required.")

        # Delete Plan Form
        st.markdown("### Delete Plan")
        with st.form("delete_plan_form"):
            plan_options = {f"{plan['name']} (ID: {plan['id']})": plan['id'] for plan in plans}
            selected_plan_display = st.selectbox("Select Plan to Delete", options=plan_options.keys())
            delete_submit_button = st.form_submit_button("Delete Selected Plan")

            if delete_submit_button and selected_plan_display:
                delete_id = plan_options[selected_plan_display]
                st.warning(f"Are you sure you want to delete plan '{selected_plan_display}'?")
                if st.button("Confirm Deletion", key=f"confirm_delete_{delete_id}"):
                    with st.spinner(f"Deleting plan {delete_id}..."):
                        res = delete_plan(delete_id)
                        try:
                            if res.status_code == 200 or res.status_code == 204:
                                st.success(f"Plan {delete_id} deleted successfully.")
                                st.rerun()
                            else:
                                resjson = res.json()
                                st.error(f"Error deleting plan: {resjson.get('message', res.text)}")
                        except Exception as e:
                            st.error(f"Failed to delete plan: {res.status_code} {res.text} | Error: {e}")
            elif delete_submit_button:
                st.error("Please select a plan to delete.")

else:
    st.warning("Please log in to access the dashboard.")