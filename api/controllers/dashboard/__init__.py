from flask import Blueprint

from libs.external_api import ExternalApi

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
api = ExternalApi(bp)


from . import index
from . import accounts
from . import plan
# from . import reset