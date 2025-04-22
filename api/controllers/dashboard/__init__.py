from flask import Blueprint

from libs.external_api import ExternalApi

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
api = ExternalApi(bp)
API_KEY = "89fisiqoo009"


from . import accounts, index, plan
# from . import reset