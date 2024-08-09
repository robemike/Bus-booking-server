#!/usr/bin/env python3

# Configuration of our flask application
import random
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from flask_cors import CORS
from customers import customer_bp, bcrypt, jwt
from driver import driver_bp
from datetime import timedelta
from flask import Flask, jsonify
from admin import admin_bp
from flask_migrate import Migrate

from models import db

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookings.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "fsbdgfnhgvjnvhmvh"+str(
    random.randint(1,1000000000000))
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["SECRET_KEY"] = "JKSRVHJVFBSRDFV"+str(random.randint(1,1000000000000))
app.json.compact = False

app.register_blueprint(customer_bp)
app.register_blueprint(driver_bp)
app.register_blueprint(admin_bp)

migrate = Migrate(app, db)
db.init_app(app)
bcrypt.init_app(app)
jwt.init_app(app)


# Logout
BLACKLIST = set()
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, decrypted_token):
    return decrypted_token['jti'] in BLACKLIST

@app.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    jti = get_jwt()["jti"]
    BLACKLIST.add(jti)
    return jsonify({"success":"Successfully logged out"}), 200


if __name__ == "__main__":
    app.run(port=5555, debug=True)