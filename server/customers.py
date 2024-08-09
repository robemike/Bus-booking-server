from flask import Blueprint, request, jsonify, make_response
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from models import Driver, Customer, Booking, db, Schedule
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)

# Create a blueprint for authentication
customer_bp = Blueprint("customer_bp", __name__, url_prefix="/")
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
            "email",
            "password",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        password = data.get("password")

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        user = Customer.query.filter_by(
            email=data["email"],
        ).first()

        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200
        else:
            return {"error": "Invalid login credentials"}, 401


class RefreshToken(Resource):
    def post(self):
        @jwt_required(refresh=True)
        def refresh():
            current_user = get_jwt_identity()
            new_access_token = create_access_token(identity=current_user)
            return {"new_access_token": new_access_token}, 200

        return refresh()
    

class Logout(Resource):
    @jwt_required(refresh=True)
    def post(self):
        jti = get_jwt_identity()
        jwt.blacklist_token(jti)
        return {"message": "Logged out successfully."}, 200
    

class Bookings(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400
        
        required_fields = [
            "departure",
            "to",
            "number_of_seats",
            "scheduled_bus_id",
            "total_cost"
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400
        
        customer_id = get_jwt_identity()
        departure = data.get('departure')
        destination = data.get('to')
        scheduled_bus_id = data.get('scheduled_bus_id')
        number_of_seats = data.get('number_of_seats')
        total_cost = data.get('total_cost')

        scheduled_bus = Schedule.query.get(scheduled_bus_id)
        if not scheduled_bus:
            return {"error": "Scheduled bus not found."}, 404
        
        if scheduled_bus.available_seats < number_of_seats:
            return {"error": "Not enough seats available."}, 400
        
        try:
            new_booking = Booking(
                departure=departure,
                to=destination,
                customer_id=customer_id,
                scheduled_bus_id=scheduled_bus_id,
                number_of_seats=number_of_seats,
                total_cost=total_cost
            )
            db.session.add(new_booking)
            scheduled_bus.available_seats -= number_of_seats
            db.session.commit()
            return {"message": "Booking created successfully.", "booking_id": new_booking.id}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
        
    @jwt_required()
    def delete(self, booking_id):
        customer_id = get_jwt_identity()

        booking = Booking.query.get_or_404(booking_id)
        if not booking:
            return {"error": "Booking not found."}, 404
        
        if booking.customer_id!= customer_id:
            return {"error": "You don't have permission to delete this booking."}, 403
        
        try:
            db.session.delete(booking)
            db.session.commit()
            return {"message": "Booking deleted successfully."}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
        
    @jwt_required()
    def get(self):
        customer_id = get_jwt_identity()

        bookings = Booking.query.filter_by(customer_id=customer_id).all()
        return [booking.serialize() for booking in bookings]


customer_api.add_resource(Signup, "/signup")
customer_api.add_resource(Login, "/login")
customer_api.add_resource(RefreshToken, "/refresh")
customer_api.add_resource(Logout, "/logout")
customer_api.add_resource(Bookings, "/bookings", "/bookings/<int:booking_id>")
