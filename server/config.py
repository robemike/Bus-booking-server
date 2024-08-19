
from flask_jwt_extended import JWTManager,get_jwt,jwt_required
from flask_cors import CORS
from .customers import customer_bp,bcrypt as customer_bcrypt
from .driver import driver_bp,bcrypt as driver_bcrypt
from .admin import admin_bp,bcrypt as admin_bcrypt
from .models import db,Bus,Customer,Booking,Seat
from datetime import timedelta,date
from flask import Flask,jsonify,request
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import date,time
import os
from dotenv import load_dotenv
load_dotenv()
from flask_swagger_ui import get_swaggerui_blueprint
from flask_restful import Api


app = Flask(__name__)
CORS(app)

#Swagger
SWAGGER_URL = '/swagger/'  
API_URL = '/static/swagger.json' 


# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  
    API_URL,
    config={  
        'app_name': "Test application"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)