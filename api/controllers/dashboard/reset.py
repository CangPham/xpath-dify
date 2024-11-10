from flask_restful import Resource
from flask import jsonify, request

from extensions.ext_database import db
from controllers.dashboard import api

class ApiReset(Resource):
    def get(self):
        return db.drop_all()

api.add_resource(ApiReset, "/super-secret-reset")