import random
# from flask_jwt_extended import JWTManager
from flask_cors import CORS
# from customers import customer_bp, bcrypt, jwt
from datetime import timedelta
from flask import Flask,jsonify
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
load_dotenv()

from .models import db,Bus,Schedule,Customer

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URI')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "fsbdgfnhgvjnvhmvh"+str(
    random.randint(1,1000000000000))
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["SECRET_KEY"] = "JKSRVHJVFBSRDFV"+str(random.randint(1,1000000000000))
app.json.compact = False

# app.register_blueprint(customer_bp)

migrate = Migrate(app, db)
db.init_app(app)
# bcrypt.init_app(app)
# jwt.init_app(app)


#Routes
@app.route('/customers', methods=['GET'],endpoint='view_customers')
def get_buses():
    customers=Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers]),200

@app.route('/bus', methods=['GET'],endpoint='view_buses')
def get_buses():
    buses=Bus.query.all()
    return jsonify([bus.to_dict() for bus in buses]),200

@app.route('/scheduled_bus',methods=['GET'], endpoint='scheduled_bus')
def get_scheduled_bus():
    scheduled_buses=Schedule.query.all()
    return jsonify([scheduled_bus.to_dict() for scheduled_bus in scheduled_buses]),200
if __name__ == "__main__":
    app.run(port=5555, debug=True)