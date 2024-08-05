from flask import Blueprint, request
from flask_restful import Resource, Api
from models import Driver, db
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token

driver_bp = Blueprint("drivers_bp", __name__, url_prefix="/driver")
driver_api = Api(driver_bp)
bcrypt = Bcrypt()


class Signup(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided"}

        required_fields = [
            "firstname",
            "lastname",
            "email",
            "password",
            "phone_number",
            "license_number",
            "experience_years",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        email = data["email"]
        firstname = data["firstname"]
        lastname = data["lastname"]
        password = data["password"]
        existing_driver = Driver.query.filter_by(
            firstname=firstname, lastname=lastname, email=email
        ).first()

        if existing_driver:
            return {"error": "Driver already exists."}, 400

        try:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            new_driver = Driver(
                firstname=firstname,
                lastname=lastname,
                email=email,
                password=hashed_password,
                phone_number=data["phone_number"],
                license_number=data["license_number"],
                experience_years=data["experience_years"],
            )
        except KeyError as e:
            return {"error": f"Missing required field: {e}"}, 400
        db.session.add(new_driver)
        db.session.commit()
        return {"success": "Driver registered successfully"}, 201


class Login(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided"}

        required_fields = ["email", "password"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        password = data.get("password")

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        driver = Driver.query.filter_by(email=data["email"]).first()

        if driver and bcrypt.check_password_hash(driver.password, password):
            access_token = create_access_token(identity=driver.id)
            return {"access_token": access_token}, 200
        else:
            return {"error": "Invalid login credentials"}, 401


driver_api.add_resource(Signup, "/signup")
driver_api.add_resource(Login, "/login")
