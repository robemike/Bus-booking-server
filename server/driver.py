from flask import Blueprint, request,jsonify
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from models import Driver, db,Bus,Schedule
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token,jwt_required,get_jwt_identity
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import date
driver_bp = Blueprint("driver_bp", __name__, url_prefix="/drivers/auth")
bcrypt = Bcrypt()
jwt = JWTManager()
driver_api = Api(driver_bp)


class ProtectedResource(Resource):
    @jwt_required()
    def get(self):
        """Get protected resource
        ---
        responses:
          200:
            description: A greeting message for the authenticated user
          401:
            description: Unauthorized
        """
        current_user = get_jwt_identity()  
        return {"message": f"Hello, user {current_user}"}

#Auth
class Signup(Resource):
    def post(self):
        """Sign up a new driver
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                firstname:
                  type: string
                lastname:
                  type: string
                license_number:
                  type: string
                experience_years:
                  type: integer
                phone_number:
                  type: integer
                email:
                  type: string
                password:
                  type: string
        responses:
          201:
            description: Driver registered successfully
          400:
            description: Error with missing fields or existing driver
        """
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
            return {"error": "Driver already exists."}, 400

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

        return {"message": "Driver registered successfully."}, 201
    
class Login(Resource):
    def post(self):
        """Driver login
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                email:
                  type: string
                license_number:
                  type: string
                password:
                  type: string
        responses:
          200:
            description: Access and refresh tokens
          401:
            description: Invalid credentials
        """
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        required_fields = [
            "email",
            "license_number",
            "password",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        user = Driver.query.filter_by(
            email=data["email"],
            license_number=data["license_number"],
        ).first()

        if user and bcrypt.check_password_hash(user.password, data["password"]):
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200
        else:
            return {"error": "Invalid Driver login credentials"}, 401

#Register Bus
class RegisterBus(Resource):
    @jwt_required()
    def post(self):
        """Register a new bus
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties: 
                username:
                  type: string
                cost_per_seat:
                  type: number
                number_of_seats:
                  type: integer
                route:
                  type: string
                travel_time:
                  type: string  # Change to string for date format
                  format: date
                number_plate:
                  type: string
        responses:
          201:
            description: Bus registered successfully
          400:
            description: Error with missing fields
          404:
            description: Driver not found
        """
        current_driver_id = get_jwt_identity()
        driver = Driver.query.get(current_driver_id)

        if not driver:
            return {"error": "Driver not found."}, 404

        data = request.get_json()
        required_fields = ['username', 'cost_per_seat', 'number_of_seats', 'route', 'travel_time', 'number_plate']

        missing_fields = [field for field in required_fields if field not in data]
        number_plate = data["number_plate"]

        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        # Convert travel_time to a date object if it's a string
        try:
            travel_time = date.fromisoformat(data['travel_time'])  # Ensure it's a valid ISO format (YYYY-MM-DD)
        except ValueError:
            return {"error": "Invalid travel_time format. Use YYYY-MM-DD."}, 400

        new_bus = Bus(
            username=data['username'],
            driver_id=current_driver_id,
            cost_per_seat=data['cost_per_seat'],
            number_of_seats=data['number_of_seats'],
            route=data['route'],
            travel_time=travel_time,
            number_plate=number_plate
        )
        db.session.add(new_bus)
        db.session.commit()

        return {"message": "Bus registered successfully."}, 201
    
#Update the Bus Price per seat
class UpdateBusCost(Resource):
    @jwt_required()
    def put(self, bus_id):
        """Update the cost per seat of a bus
        ---
        parameters:
          - name: bus_id
            in: path
            required: true
            type: integer
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                cost_per_seat:
                  type: number
        responses:
          200:
            description: Cost per seat updated successfully
          400:
            description: Cost per seat is required
          404:
            description: Bus not found or permission denied
        """
        current_driver_id = get_jwt_identity()
        bus = Bus.query.filter_by(id=bus_id, driver_id=current_driver_id).first()

        if not bus:
            return {"error": "Bus not found or you do not have permission to update this bus."}, 404

        data = request.get_json()
        if 'cost_per_seat' not in data:
            return {"error": "Cost per seat is required."}, 400

        bus.cost_per_seat = data['cost_per_seat']
        db.session.commit()

        return {"message": "Cost per seat updated successfully."}, 200

class GetBusesByDriver(Resource):
    @jwt_required()
    def get(self):
        """Get buses by the current driver
        ---
        responses:
          200:
            description: List of buses for the driver
          404:
            description: No buses found for this driver
        """
        current_driver_id = get_jwt_identity()
        buses = Bus.query.filter_by(driver_id=current_driver_id).all()

        if not buses:
            return {"message": "No buses found for this driver."}, 404

        return [bus.to_dict() for bus in buses], 200

class GetScheduledBuses(Resource):
    @jwt_required()
    def get(self):
        """Get all scheduled buses
        ---
        responses:
          200:
            description: List of scheduled buses
          404:
            description: No scheduled buses found
        """
        scheduled_buses = Schedule.query.all()
        if not scheduled_buses:
            return jsonify({"message": "No scheduled buses found."}), 404

        return jsonify([{
            'id': scheduled_bus.id,
            'bus_id': scheduled_bus.bus_id,
            'departure_time': scheduled_bus.departure_time.isoformat(),
            'arrival_time': scheduled_bus.arrival_time.isoformat(),
            'travel_date': scheduled_bus.travel_date.isoformat(),
            'available_seats': scheduled_bus.available_seats,
            'occupied_seats': scheduled_bus.occupied_seats,
            'bus': scheduled_bus.bus.to_dict() if scheduled_bus.bus else None
        } for scheduled_bus in scheduled_buses]), 200

# Register the resources with the API
driver_api.add_resource(RegisterBus, "/register/buses")
driver_api.add_resource(UpdateBusCost, "/buses/<int:bus_id>/cost")
driver_api.add_resource(GetBusesByDriver, "/buses")
driver_api.add_resource(Signup, "/signup")
driver_api.add_resource(Login, "/login")
driver_api.add_resource(ProtectedResource, "/protected")
driver_api.add_resource(GetScheduledBuses, "/scheduled_buses")
