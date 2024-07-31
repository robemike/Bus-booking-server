from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from models import Driver, Customer, Admin, db
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token

# Create a blueprint for authentication
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/authentication')
bcrypt = Bcrypt()
jwt = JWTManager()
auth_api = Api(auth_bp)

class Signup(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided"}
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"error": "Missing required fields."})

        existing_user = Customer.query.filter_by(email=email).first()

        if existing_user:
            return {"message": 'Email address already in exists'}, 400
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = Customer(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return {"message": "Member registered successfully."}
        
class Login(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return jsonify({"error": "No input data provided."})
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"error": "Missing required fields."}), 400
        
        user = Customer.query.filter_by(username=username, email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.id)
            # refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token}, 200
        else:
            return jsonify({"error": 'Invalid login credentials'}), 401
        
auth_api.add_resource(Signup, '/signup')
auth_api.add_resource(Login, '/login')