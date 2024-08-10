from flask import Blueprint, request,jsonify
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from .models import Driver, db,Bus,Schedule
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token,jwt_required,get_jwt_identity
from datetime import time,datetime


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
        return {"message": f"Hello, Driver, your ID is {current_user}"}

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
            return jsonify({"error": "No input data provided."}), 400

        required_fields = [
            "firstname",
            "lastname",
            "license_number",
            "experience_years",
            "phone_number",
            "email",
            "password",
        ]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]

        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        email = data["email"]
        license_number = data["license_number"]

        existing_driver = Driver.query.filter_by(
            email=email,
            license_number=license_number,
        ).first()

        if existing_driver:
            return jsonify({"error": "Driver already exists."}), 400

        try:
            hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
            new_driver = Driver(
                firstname=data["firstname"],
                lastname=data["lastname"],
                email=email,
                password=hashed_password,
                phone_number=data["phone_number"],
                license_number=license_number,
                experience_years=data["experience_years"],
            )
            db.session.add(new_driver)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

        return jsonify({"success": "Driver registered successfully"}), 201


    
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

        driver = Driver.query.filter_by(email=data["email"]).first()

        if driver and bcrypt.check_password_hash(driver.password, data["password"]):
            access_token = create_access_token(identity=driver.id)
            refresh_token = create_refresh_token(identity=driver.id)
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
            return jsonify({"error": "Driver not found."}), 404

        data = request.get_json()
        required_fields = ['username', 'cost_per_seat', 'number_of_seats', 'route', 'travel_time', 'number_plate']

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400


        try:
            travel_time = time.fromisoformat(data['travel_time'])  
        except ValueError:
            return jsonify({"error": "Invalid travel_time format. Use YYYY-MM-DD."}), 400

        new_bus = Bus(
            username=data['username'],
            driver_id=current_driver_id,
            cost_per_seat=data['cost_per_seat'],
            number_of_seats=data['number_of_seats'],
            route=data['route'],
            travel_time=travel_time,
            number_plate=data['number_plate']
        )

        try:
            db.session.add(new_bus)
            db.session.commit()
        except Exception as e:
            db.session.rollback() 
            return jsonify({"error": str(e)}), 500  

        return jsonify({"message": "Bus registered successfully."}), 201


    

#Scheduling Buses
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
            return {"message": "No scheduled buses found."}, 404

     
        data = [{
            "id": scheduled_bus.id,
            'bus_id': scheduled_bus.bus_id,
            'departure_time': scheduled_bus.departure_time.isoformat(),
            'arrival_time': scheduled_bus.arrival_time.isoformat(),
            'travel_date': scheduled_bus.travel_date.isoformat(),
            'available_seats': scheduled_bus.available_seats,
            'occupied_seats': scheduled_bus.occupied_seats,
            'bus': {
                'id': scheduled_bus.bus.id,
                'username': scheduled_bus.bus.username,
                'number_plate': scheduled_bus.bus.number_plate,
                
            } if scheduled_bus.bus else None
        } for scheduled_bus in scheduled_buses]

        return data, 200
        
from datetime import datetime

class ScheduledBuses(Resource):
    @jwt_required()
    def post(self):
        """Create a new scheduled bus
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                bus_id:
                  type: integer
                departure_time:
                  type: string
                  format: time
                arrival_time:
                  type: string
                  format: time
                travel_date:
                  type: string
                  format: date
                available_seats:
                  type: integer
                occupied_seats:
                  type: integer
        responses:
          201:
            description: Scheduled bus created successfully
          400:
            description: Error with missing fields or invalid data
        """
        data = request.get_json()

        required_fields = ['bus_id', 'departure_time', 'arrival_time', 'travel_date', 'available_seats', 'occupied_seats']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        try:
            departure_datetime = datetime.strptime(f"{data['travel_date']} {data['departure_time']}", "%Y-%m-%d %H:%M:%S")
            arrival_datetime = datetime.strptime(f"{data['travel_date']} {data['arrival_time']}", "%Y-%m-%d %H:%M:%S")

            new_schedule = Schedule(
                bus_id=data['bus_id'],
                departure_time=departure_datetime, 
                arrival_time=arrival_datetime,     
                travel_date=data['travel_date'],       
                available_seats=data['available_seats'],
                occupied_seats=data['occupied_seats'],
            )
            db.session.add(new_schedule)
            db.session.commit()

            return {"message": "Scheduled bus created successfully."}, 201
        except Exception as e:
            db.session.rollback()  
            return {"error": "Failed to create scheduled bus.", "details": str(e)}, 500
    
 

# Register the resources with the API
driver_api.add_resource(RegisterBus, "/register/buses")
driver_api.add_resource(Signup, "/signup")
driver_api.add_resource(Login, "/login")
driver_api.add_resource(ProtectedResource, "/protected")
driver_api.add_resource(GetScheduledBuses, "/view_scheduled_buses")
driver_api.add_resource(ScheduledBuses, "/scheduled_buses")
