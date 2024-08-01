#!/usr/bin/env python3

# Configuration of our flask application
import random
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from customer import customer_bp, bcrypt, jwt
from datetime import timedelta
from flask import Flask
from flask_migrate import Migrate

from models import db

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = "fsbdgfnhgvjnvhmvh"+str(random.randint(1,1000000000000))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config["SECRET_KEY"] = "JKSRVHJVFBSRDFV"+str(random.randint(1,1000000000000))
app.json.compact = False

app.register_blueprint(customer_bp)

migrate = Migrate(app, db)
db.init_app(app)
bcrypt.init_app(app)
jwt.init_app(app)

if __name__ == '__main__':
    app.run(port=5555, debug=True)