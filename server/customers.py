from flask import request,make_response,session,Blueprint
from flask_restful import Resource,Api
from .models import Customer, Booking,Bus,Schedule,Seat,Admin,Driver
from datetime import datetime
from .config import jwt,db,bcrypt
from flask_jwt_extended import create_access_token,create_refresh_token,get_jwt_identity,jwt_required,current_user
import logging



customer_bp = Blueprint("customer_bp", __name__, url_prefix="/")
customer_api = Api(customer_bp)


class ProtectedResource(Resource):
    def get(self):
        current_user = get_jwt_identity() 
        return {"message": f"Hello, Customer {current_user}"}
    
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    role = jwt_data.get("role")  # Extract the role from the JWT claims

    if role:
        if role == 'customer':
            return Customer.query.filter_by(id=identity).one_or_none()
        elif role == 'admin':
            return Admin.query.filter_by(id=identity).one_or_none()
        elif role == 'driver':
            return Driver.query.filter_by(id=identity).one_or_none()

    return None



class CheckSession(Resource):
    @jwt_required()
    def get(self):
        return make_response(current_user.to_dict(), 200)


customer_api.add_resource(CheckSession, "/check_session", endpoint="check_session")

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
        access_token = create_access_token(identity=new_customer.id, additional_claims={"role": new_customer.role})

        return {"message": "Customer registered successfully","access_token":access_token, "new_customer":new_customer.to_dict()}, 201


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

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        password = data.get("password")
        user = Customer.query.filter_by(email=data["email"]).first()

        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
            refresh_token = create_refresh_token(identity=user.id,additional_claims={"role": user.role} )
            
            # Serialize the Customer object into a dictionary
            customer_data = {
                "id": user.id,
                "email": user.email,
                "firstname": user.firstname,
                # Add any other relevant fields
            }

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "customer": user.to_dict()
            }, 200
        else:
            return {"error": "Invalid login credentials"}, 401

    
class ViewBookings(Resource):
    def get(self, customer_id):
        # Assuming `customer_id` is now passed as a path parameter

        # Validate the customer_id if necessary
        if not customer_id:
            return {"message": "Customer ID is required."}, 400

        bookings = Booking.query.filter_by(customer_id=customer_id).all()

        if not bookings:
            return {"message": "No bookings found."}, 404

        # Retrieve the customer object associated with the bookings
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return {"message": "Customer not found."}, 404

        # Manually construct the response data
        bookings_data = [
            {
                **booking.to_dict(),  # Assuming to_dict() doesn't take any arguments
                'phone_number': customer.phone_number
            }
            for booking in bookings
        ]

        # Return the list of bookings along with the customer's phone number
        return make_response({"bookings": bookings_data}, 200)
    
class ViewAllBookings(Resource):
    def get(self):
        """Retrieve all bookings."""
        try:
            # Query all bookings
            bookings = Booking.query.all()
            
            if not bookings:
                return {"message": "No bookings found."}, 404

            # Serialize bookings
            bookings_list = [booking.to_dict() for booking in bookings]
            return (bookings_list)
        
        except Exception as e:
            return {"error": str(e)}, 500

class AddBookings(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400
        
        required_fields = [
            "departure_time",  # travel_time
            "current_address",  # from
            "number_of_seats",
            "destination",  # to
            "bus_id",
            "selected_seats",
        ]
        
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400
        
        # Get customer_id from JWT
        customer_id = get_jwt_identity()

        # Extract data from the request
        departure_time_str = data.get('departure_time')
        destination = data.get('destination')
        number_of_seats = data.get('number_of_seats')
        current_address = data.get('current_address')
        bus_id = data.get('bus_id')  
        selected_seats = data.get('selected_seats')

        # Convert departure_time from string to a time object
        try:
            departure_time = datetime.strptime(departure_time_str, "%H:%M:%S").time()
        except ValueError:
            return {"error": "Invalid time format. Use HH:MM:SS."}, 400

        # Check if the bus exists
        bus = Bus.query.get(bus_id)
        if not bus:
            return {"error": "Bus not found."}, 404

        # Calculate total cost
        total_cost = bus.cost_per_seat * number_of_seats

        # Create a new booking
        try:
            new_booking = Booking(
                departure_time=departure_time,
                destination=destination,
                customer_id=customer_id,  
                number_of_seats=number_of_seats,
                current_address=current_address,
                bus_id=bus_id, 
                total_cost=total_cost,
                selected_seats=selected_seats 
            )
            db.session.add(new_booking)
            db.session.commit()
            return {"message": "Booking created successfully.", "booking_id": new_booking.id}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
        
class UpdateBooking(Resource):
    def put(self, booking_id):
        """Update a booking by ID."""
        data = request.get_json()
        bus_id = data.get('bus_id') 
        # Validate bus_id
        if bus_id is None:
            return {"message": "bus_id is required."}, 400

        booking = Booking.query.get(booking_id)
        if not booking:
            return {"message": "Booking not found."}, 404

        booking.bus_id = bus_id  
        db.session.commit()

        return {"message": "Booking updated successfully."}, 200
    
class DeleteBooking(Resource):
    def delete(self, booking_id):
        """Delete a booking by its ID.
        ---
        parameters:
          - name: booking_id
            in: path
            type: integer
            required: true
            description: The ID of the booking to delete
        responses:
          200:
            description: Booking successfully deleted
          404:
            description: Booking not found
        """
        # Query the database for the booking associated with the provided ID
        booking = Booking.query.get(booking_id)

        if not booking:
            return {"message": "Booking not found."}, 404

        # Delete the booking
        db.session.delete(booking)
        db.session.commit()

        return {"message": "Booking successfully deleted."}, 200
    
class BookSeat(Resource):

    def post(self):
        data = request.get_json()
        bus_id = data.get('bus_id')
        selected_seats = data.get('selected_seats')

        if not bus_id or not selected_seats:
            return {'error': 'bus_id and selected_seats are required'}, 400

        schedule = Schedule.query.filter_by(bus_id=bus_id).first()

        if not schedule:
            return {'error': 'Schedule not found'}, 404
        
        # Check the number of seats available
        available_seats = schedule.available_seats
        number_of_seats_to_book = len(selected_seats)

        # if number_of_seats_to_book > available_seats:
        #     return {'error': 'Not enough seats available'}, 400

        # Update the occupied seats and available seats
        schedule.occupied_seats += number_of_seats_to_book
        schedule.available_seats -= number_of_seats_to_book

        # Ensure available_seats does not go below zero
        if schedule.available_seats < 0:
            schedule.available_seats = 0

        # Update seat statuses
        for seat_number in selected_seats:
            seat = Seat.query.filter_by(bus_id=bus_id, seat_number=seat_number).first()
            if seat:
                if seat.status == 'available':  # Check if seat is available before booking
                    seat.status = 'booked'
                else:
                    # If any seat is already booked, rollback and return an error
                    db.session.rollback()
                    return {'error': f'Seat {seat_number} is already booked'}, 400

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error committing to the database: {e}")
            return {'error': 'Internal server error'}, 500

        return {'message': 'Seats booked successfully!'}, 200

customer_api.add_resource(Signup, "/signup")
customer_api.add_resource(Login, "/login")
# customer_api.add_resource(RefreshToken, "/refresh")
customer_api.add_resource(ProtectedResource, "/protected")
customer_api.add_resource(AddBookings, "/bookings",)
customer_api.add_resource(ViewBookings, '/view_bookings/<int:customer_id>')
customer_api.add_resource(ViewAllBookings, '/view_bookings')
customer_api.add_resource(UpdateBooking, '/update_bookings')
customer_api.add_resource(DeleteBooking, '/delete_booking/<int:booking_id>')
customer_api.add_resource(BookSeat, '/book-seats')