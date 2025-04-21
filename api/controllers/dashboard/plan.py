from flask import jsonify, request
from flask_restful import Resource
from pydantic import BaseModel

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
            object_plans = [PlanModel.model_validate(plan) for plan in system_custom_info.value]
        
        return jsonify([plan.dict() for plan in object_plans])
    
    def put(self):
        # Get the request data
        data = request.get_json()

        plans = [PlanModel.model_validate(plan) for plan in data]
        # Get the existing system custom info
        system_custom_info = db.session.query(SystemCustomInfo).filter(
            SystemCustomInfo.name == "plan"
        ).first()
        
        # Create a new system custom info if it doesn't exist
        if not system_custom_info:
            system_custom_info = SystemCustomInfo(name="plan", value=[])
        
        # Update the existing plans with the new data
        system_custom_info.value = [plan.dict() for plan in plans]

        # Commit the changes to the database
        db.session.add(system_custom_info)
        db.session.commit()

        # Return a success message
        return jsonify({"status": "success", "message": "Plan updated successfully."})