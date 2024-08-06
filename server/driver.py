from flask import Blueprint, request
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from models import Driver, db
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token

driver_bp = Blueprint("driver_bp", __name__, url_prefix="/drivers/authentication")
bcrypt = Bcrypt()
jwt = JWTManager()
driver_api = Api(driver_bp)


#Auth
class Signup(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        required_fields = [
            "firstname",
            "lastname",
            "license_number",
            "experience_years",
            "phone_number",
            "email",
            "password",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        email = data["email"]
        firstname = data["firstname"]
        lastname = data["lastname"]
        license_number = data["license_number"]
        experience_years = data["experience_years"]

        existing_customer = Driver.query.filter_by(
            firstname=firstname, lastname=lastname, email=email
        ).first()

        if existing_customer:
            return {"error": "User already exists."}, 400

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        new_customer = Driver(
            firstname=firstname,
            lastname=lastname,
            email=email,
            license_number=license_number,
            experience_years=experience_years,
            password=hashed_password,
            phone_number=data["phone_number"],
        )

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
            "license_number",
            "experience_years",
            "phone_number",
            "password",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400
        

        user = Driver.query.filter_by(
            firstname=data["firstname"],
            lastname=data["lastname"],
            email=data["email"],
            license_number=data["license_number"],
            experience_years=data["experience_years"],
            phone_number=data["phone_number"],
        ).first()

        if user and bcrypt.check_password_hash(user.password, data["password"]):
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200
        else:
            return {"error": "Invalid login credentials"}, 401

driver_api.add_resource(Signup, "/signup")
driver_api.add_resource(Login, "/login")
