from flask import jsonify, request
from flask_restful import Resource
from pydantic import BaseModel
from datetime import date

from controllers.dashboard import api, API_KEY
from controllers.console import api as api_console
from configs import dify_config
from extensions.ext_database import db
from models.system_custom_info import SystemCustomInfo
from models.payments_history_custom import PaymentsHistoryCustom
from models.account import Account

class FeatureModel(BaseModel):
    members: int = 1
    apps: int = dify_config.user_account_max_of_apps
    vector_space: int = dify_config.user_account_max_vector_space
    knowledge_rate_limit: int = dify_config.user_account_knowledge_rate_limit
    annotation_quota_limit: int = dify_config.user_account_max_annotation_quota_limit
    documents_upload_quota: int = dify_config.user_account_max_documents_upload_quota

class PlanModel(BaseModel):
    id: str
    name: str
    description: str
    price: float
    plan_expiration: int   # number of days until expiration
    features: FeatureModel

class PaymentSettingsModel(BaseModel):
    access_token: str = "123456"
    account_name: str = ""
    account_id: str = ""  # Corrected typo: acouunt_id -> account_id
    bank_id: str = ""

class PaymentHistoryModel(BaseModel):
    id: str
    type: str
    transactionID: str
    amount: float
    description: str
    date: str
    bank: str

class ApiPaymentSettings(Resource):
    def get(self):
        # Get all system custom info
        system_custom_info = db.session.query(SystemCustomInfo).filter(
            SystemCustomInfo.name.in_(["payment_settings"])
        ).first()

        # Check if system custom info exists
        if not system_custom_info:
            # Create a new system custom info if it doesn't exist
            system_custom_info = SystemCustomInfo(name="payment_settings", value=PaymentSettingsModel().model_dump(mode='json'))
            # Add default payment settings
            db.session.add(system_custom_info)
            db.session.commit()

        # Pydantic v2 uses model_dump() instead of dict()
        # Ensure the model loaded from DB is validated against the current model definition
        settings_data = system_custom_info.value
        # Add default values for potentially missing fields if loaded from an older schema
        validated_settings = PaymentSettingsModel.model_validate(settings_data)
        return jsonify(validated_settings.model_dump(mode='json'))

    def put(self):
        # Get the request data
        data = request.get_json()

        # Get the existing system custom info
        system_custom_info = db.session.query(SystemCustomInfo).filter(
            SystemCustomInfo.name == "payment_settings"
        ).first()

        # Create a new system custom info if it doesn't exist
        if not system_custom_info:
            system_custom_info = SystemCustomInfo(name="payment_settings", value=PaymentSettingsModel().model_dump(mode='json'))

        # Pydantic v2 uses model_validate
        try:
            payment_settings = PaymentSettingsModel.model_validate(data)
        except Exception as e:
             return jsonify({"status": "error", "message": f"Invalid data format: {e}"}), 400

        # Update the existing payment settings with the new data
        system_custom_info.value = payment_settings.model_dump(mode='json')

        # Commit the changes to the database
        db.session.add(system_custom_info)
        db.session.commit()

        # Return a success message
        return jsonify({"status": "success", "message": "Payment settings updated successfully."})

class ApiPlan(Resource):
    def get(self):
        # Get all system custom info
        system_custom_info = db.session.query(SystemCustomInfo).filter(
            SystemCustomInfo.name.in_(["plan"])
        ).first()

        object_plans = []

        # Check if system custom info exists
        if not system_custom_info:
           # Create a new system custom info if it doesn't exist
            system_custom_info = SystemCustomInfo(name="plan", value=[])
            # Add default plans
            db.session.add(system_custom_info)
            db.session.commit()
        else:
            # Convert the value from list[json] to list[PlanModel]
            # Skip plans with string expiration date
            raw_plans = system_custom_info.value
            list_of_plans = []
            for plan in raw_plans:
                exp = plan.get("plan_expiration")
                if isinstance(exp, str):
                    continue
                list_of_plans.append(plan)
            object_plans = [PlanModel.model_validate(plan) for plan in list_of_plans]
        
        # Pydantic v2 uses model_dump() instead of dict()
        return jsonify([plan.model_dump(mode='json') for plan in object_plans])
    
    def put(self):
        # Get the request data
        data = request.get_json()

        # Pydantic v2 uses model_validate
        plans = [PlanModel.model_validate(plan) for plan in data]
        # Get the existing system custom info
        system_custom_info = db.session.query(SystemCustomInfo).filter(
            SystemCustomInfo.name == "plan"
        ).first()
        
        # Create a new system custom info if it doesn't exist
        if not system_custom_info:
            system_custom_info = SystemCustomInfo(name="plan", value=[])
        
        # Update the existing plans with the new data
        # Pydantic v2 uses model_dump() instead of dict()
        system_custom_info.value = [plan.model_dump(mode='json') for plan in plans]

        # Commit the changes to the database
        db.session.add(system_custom_info)
        db.session.commit()

        # Return a success message
        return jsonify({"status": "success", "message": "Plan updated successfully."})

def decode_description_pay(description):
    # Todo: format description: .*?account plan([0-9]+).*?
    # Get plan id from description

class ApiPlanWebhook(Resource):
    # Todo: Implement webhook

api.add_resource(ApiPlanWebhook, "/webhook/plan")    
api.add_resource(ApiPlan, "/plans")
api.add_resource(ApiPaymentSettings, "/payment_settings")
api_console.add_resource(ApiPlan, "/custom/plans")
api_console.add_resource(ApiPaymentSettings, "/custom/payment_settings")