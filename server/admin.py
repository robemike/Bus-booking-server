from flask import Blueprint
from flask_restful import Api, Resource
from models import Admin

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

class ViewAllUsers(Resource):
    def get(self):

         
        pass