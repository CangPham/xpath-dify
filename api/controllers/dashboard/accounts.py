from flask_restful import Resource
from flask import jsonify, request

from extensions.ext_database import db
from controllers.dashboard import api
from controllers.dashboard.json import jsonify_sqlalchemy

from models.account import Account

class ApiAccounts(Resource):
    def get(self, account_id=None):
        if account_id:
            account = db.session.query(Account).filter_by(id=account_id).first()
            if account:
                def account_to_dict(account):
                    return {
                        "id": account.id,
                        "name": account.name,
                        "email": account.email,
                        "status": account.status,

                        "month_before_banned": account.month_before_banned,
                        "max_of_apps": account.max_of_apps,
                        "max_vector_space": account.max_vector_space,
                        "max_annotation_quota_limit": account.max_annotation_quota_limit,
                        "max_documents_upload_quota": account.max_documents_upload_quota,

                        "last_login_at": account.last_login_at,
                        "last_login_ip": account.last_login_ip,
                        "last_active_at": account.last_active_at,
                        "created_at": account.created_at,
                        "updated_at": account.updated_at
                    }
                return jsonify(account_to_dict(account))
            else:
                return {"status": "error", "message": "Account not found."}, 404
        else:
            accounts = db.session.query(Account).all()
            def account_to_dict(account):
                return {
                    "id": account.id,
                    "name": account.name,
                    "email": account.email,
                    "status": account.status,
                    
                    "month_before_banned": account.month_before_banned,
                    "max_of_apps": account.max_of_apps,
                    "max_vector_space": account.max_vector_space,
                    "max_annotation_quota_limit": account.max_annotation_quota_limit,
                    "max_documents_upload_quota": account.max_documents_upload_quota,

                    "max_of_apps": account.max_of_apps,
                    "last_login_at": account.last_login_at,
                    "last_login_ip": account.last_login_ip,
                    "last_active_at": account.last_active_at,
                    "created_at": account.created_at,
                    "updated_at": account.updated_at
                }
            return jsonify([account_to_dict(account) for account in accounts])
    
    def put(self):
        accounts = request.json
        for account in accounts:
            iter_acc = db.session.query(Account).get(account["id"])
            iter_acc.status = account["status"]
            iter_acc.month_before_banned = account["month_before_banned"]
            iter_acc.max_of_apps = account["max_of_apps"]
            iter_acc.max_vector_space = account["max_vector_space"]
            iter_acc.max_annotation_quota_limit = account["max_annotation_quota_limit"]
            iter_acc.max_documents_upload_quota = account["max_documents_upload_quota"]

        db.session.commit()
        return {
            "status": "success",
            "message": "Accounts updated successfully"
        }

    def delete(self, account_id):
        account = db.session.query(Account).get(account_id)
        if account:
            db.session.delete(account)
            db.session.commit()
            return {"status": "success", "message": f"Account {account_id} deleted."}, 200
        else:
            return {"status": "error", "message": f"Account {account_id} not found."}, 404

api.add_resource(ApiAccounts, "/accounts", "/accounts/<string:account_id>")