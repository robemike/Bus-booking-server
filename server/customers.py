from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from models import Driver, Customer, Admin, db
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token

# Create a blueprint for authentication
customer_bp = Blueprint("customer_bp", __name__, url_prefix="/authentication")
bcrypt = Bcrypt()
jwt = JWTManager()
customer_api = Api(customer_bp)


class Signup(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        required_fields = [
            "firstname",
            "lastname",
            "email",
            "password",
            "address",
            "phone_number",
            "ID_or_Passport",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        email = data["email"]
        firstname = data["firstname"]
        lastname = data["lastname"]
        existing_customer = Customer.query.filter_by(
            firstname=firstname, lastname=lastname, email=email
        ).first()

        if existing_customer:
            return {"error": "User already exists."}, 400

        try:
            hashed_password = bcrypt.generate_password_hash(data["password"]).decode(
                "utf-8"
            )
            new_customer = Customer(
                firstname=firstname,
                lastname=lastname,
                email=email,
                password=hashed_password,
                address=data["address"],
                phone_number=data["phone_number"],
                ID_or_Passport=data["ID_or_Passport"],
            )
        except KeyError as e:
            return {"error": f"Missing required field: {e}"}, 400
        db.session.add(new_customer)
        db.session.commit()

        return {"message": "User registered successfully."}, 201


class Login(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        required_fields = [
            "firstname",
            "lastname",
            "email",
            "password",
            "address",
            "phone_number",
            "ID_or_Passport",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        password = data.get("password")

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        user = Customer.query.filter_by(
            firstname=data["firstname"],
            lastname=data["lastname"],
            email=data["email"],
            address=data["address"],
            phone_number=data["phone_number"],
            ID_or_Passport=data["ID_or_Passport"],
        ).first()

        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.id)
            return {"access_token": access_token}, 200
        else:
            return {"error": "Invalid login credentials"}, 401


customer_api.add_resource(Signup, "/signup")
customer_api.add_resource(Login, "/login")
