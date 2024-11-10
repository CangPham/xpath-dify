from flask_restful import Resource
from flask import jsonify, request

from extensions.ext_database import db
from controllers.dashboard import api
from controllers.dashboard.json import jsonify_sqlalchemy

from models.account import Account

class ApiAccounts(Resource):
    def get(self):
        accounts = Account.query.all()
        def account_to_dict(account):
            return {
                "id": account.id,
                "name": account.name,
                "email": account.email,
                "status": account.status,
                "last_login_at": account.last_login_at,
                "last_login_ip": account.last_login_ip,
                "last_active_at": account.last_active_at,
                "created_at": account.created_at,
                "updated_at": account.updated_at
            }
        return jsonify([account_to_dict(account) for account in accounts])
    
    def post(self):
        accounts = request.json
        for account in accounts:
            iter_acc = Account.query.get(account["id"])
            iter_acc.status = account["status"]
        db.session.commit()
        return {
            "status": "success",
            "message": "Accounts updated successfully"
        }

api.add_resource(ApiAccounts, "/accounts")