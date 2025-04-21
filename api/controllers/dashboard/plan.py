from flask import jsonify, request
from flask_restful import Resource
from pydantic import BaseModel
from datetime import date

from controllers.dashboard import api
from configs import dify_config
from extensions.ext_database import db
from models.system_custom_info import SystemCustomInfo


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
    
api.add_resource(ApiPlan, "/plans")