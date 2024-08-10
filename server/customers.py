from flask import Blueprint, request
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from .models import Customer, Booking, db,Bus
from datetime import datetime
from flask_jwt_extended import JWTManager,create_access_token,create_refresh_token,get_jwt_identity,jwt_required


customer_bp = Blueprint("customer_bp", __name__, url_prefix="/auth")
bcrypt = Bcrypt()
jwt = JWTManager()
customer_api = Api(customer_bp)

class ProtectedResource(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity() 
        return {"message": f"Hello, Customer {current_user}"}

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
            "id_or_passport",
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
            return {"error": "Customer already exists."}, 400

        try:
            hashed_password = bcrypt.generate_password_hash(data["password"]).decode(
                "utf-8"
            )
            new_customer = Customer(
                firstname=firstname,
                lastname=lastname,
                email=email,
                address=data["address"],
                password=hashed_password,
                phone_number=data["phone_number"],
                id_or_passport=data["id_or_passport"],
            )
        except KeyError as e:
            return {"error": f"Missing required field: {e}"}, 400
        db.session.add(new_customer)
        db.session.commit()

        return {"message": "Customer registered successfully."}, 201


class Login(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        required_fields = [
            "email",
            "password"
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


# class RefreshToken(Resource):
#     def post(self):
#         @jwt_required(refresh=True)
#         def refresh():
#             current_user = get_jwt_identity()
#             new_access_token = create_access_token(identity=current_user)
#             return {"new_access_token": new_access_token}, 200

#         return refresh()
    
class ViewBookings(Resource):
    @jwt_required()
    def get(self):
        """Retrieve all bookings for the authenticated customer.
        ---
        responses:
          200:
            description: A list of bookings for the customer
          404:
            description: No bookings found
        """
        customer_id = get_jwt_identity()  # Get the current customer's ID

        # Query the database for bookings associated with this customer
        bookings = Booking.query.filter_by(customer_id=customer_id).all()

        if not bookings:
            return {"message": "No bookings found."}, 404

        # Return the list of bookings
        return [{
            'id': booking.id,
            'customer_id': booking.customer_id,
            'bus_id': booking.bus_id,
            'booking_date': booking.booking_date.isoformat(),
            'number_of_seats': booking.number_of_seats,
            'total_cost': booking.total_cost,
            'destination': booking.destination,
            'departure_time': str(booking.departure_time),
            'current_address': booking.current_address

        } for booking in bookings], 200
    
class AddBookings(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400
        
        required_fields = [
            "departure_time", 
            "current_address",
            "number_of_seats",
            "destination", 
            "bus_id"  
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400
        
        customer_id = get_jwt_identity()
        departure_time_str = data.get('departure_time')
        destination = data.get('destination')
        number_of_seats = data.get('number_of_seats')
        current_address = data.get('current_address')
        bus_id = data.get('bus_id')  # Retrieve bus_id from request data

        # Convert departure_time from string to a time object
        try:
            departure_time = datetime.strptime(departure_time_str, "%H:%M:%S").time()
        except ValueError:
            return {"error": "Invalid time format. Use HH:MM:SS."}, 400

        bus = Bus.query.get(bus_id)
        if not bus:
            return {"error": "Bus not found."}, 404

        total_cost = bus.cost_per_seat * number_of_seats

        try:
            new_booking = Booking(
                departure_time=departure_time,
                destination=destination,
                customer_id=customer_id,
                number_of_seats=number_of_seats,
                current_address=current_address,
                bus_id=bus_id, 
                total_cost=total_cost  
            )
            db.session.add(new_booking)
            db.session.commit()
            return {"message": "Booking created successfully.", "booking_id": new_booking.id}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
        


customer_api.add_resource(Signup, "/signup")
customer_api.add_resource(Login, "/login")
# customer_api.add_resource(RefreshToken, "/refresh")
customer_api.add_resource(ProtectedResource, "/protected")
customer_api.add_resource(AddBookings, "/bookings",)
customer_api.add_resource(ViewBookings, '/view_bookings')
