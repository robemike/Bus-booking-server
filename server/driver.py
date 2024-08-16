from flask import Blueprint, request,jsonify,make_response
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from .models import Driver, db,Bus,Schedule,Customer,Seat
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token,jwt_required,get_jwt_identity
from datetime import datetime


driver_bp = Blueprint("driver_bp", __name__, url_prefix="/")
bcrypt = Bcrypt()
jwt = JWTManager()
driver_api = Api(driver_bp)


class ProtectedResource(Resource):
    # @jwt_required()
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
class RegisterBuses(Resource):
    # @jwt_required()
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400
        
        required_fields = ["username", "cost_per_seat", "number_of_seats", "route", "travel_time", "number_plate", "image"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        try:
            travel_time_str = data.get('travel_time')
            travel_time = datetime.strptime(travel_time_str, "%H:%M:%S").time()
            
            new_bus = Bus(
                username=data.get('username'),
                cost_per_seat=int(data.get('cost_per_seat')),
                number_of_seats=int(data.get('number_of_seats')),
                route=data.get('route'),
                travel_time=travel_time, 
                number_plate=data.get('number_plate'),
                image=data.get('image'),                
            )
            
            db.session.add(new_bus)
            db.session.commit()

            seats = []
            for seat_num in range(1, new_bus.number_of_seats + 1):
                seat = Seat(
                    seat_number=f"S{seat_num:03}",  
                    bus_id=new_bus.id
                )
                seats.append(seat)
            db.session.add_all(seats)
            db.session.commit()
            
            return {"message": "Bus added successfully.", "bus_id": new_bus.id}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

        
class EditBuses(Resource):
    def patch(self, bus_id):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        bus = Bus.query.get(bus_id)
        if not bus:
            return {"error": "Bus not found."}, 404

        # Define required fields
        required_fields = ["username","cost_per_seat", "number_of_seats", "route", "travel_time", "number_plate", "image"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {
                "warning": f"Missing fields: {', '.join(missing_fields)}. No changes made to these fields."
            }, 400

        try:
            # Update the fields if they are provided in the request
            if 'username' in data:
                bus.username = data['username']
            if 'cost_per_seat' in data:
                bus.cost_per_seat = int(data['cost_per_seat'])
            if 'number_of_seats' in data:
                old_seats = int(bus.number_of_seats)
                new_seats = int(data['number_of_seats'])
                bus.number_of_seats = new_seats

                if new_seats > old_seats:
                    new_seat_numbers = range(old_seats + 1, new_seats + 1)
                    for seat_num in new_seat_numbers:
                        new_seat = Seat(
                            seat_number=f"S{seat_num:03}",
                            bus_id=bus.id
                        )
                        db.session.add(new_seat)
                elif new_seats < old_seats:
                    excess_seats = Seat.query.filter(Seat.bus_id == bus.id).order_by(Seat.id.desc()).limit(old_seats - new_seats).all()
                    for seat in excess_seats:
                        db.session.delete(seat)
            if 'route' in data:
                bus.route = data['route']
            if 'travel_time' in data:
                travel_time_str = data['travel_time']
                bus.travel_time = datetime.strptime(travel_time_str, "%H:%M:%S").time()
            if 'number_plate' in data:
                bus.number_plate = data['number_plate']
            if 'image' in data:
                bus.image = data['image']

            db.session.commit()
            return {"message": "Bus updated successfully."}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

        

class ViewBusesByDriver(Resource):
    # @jwt_required()
    def get(self, driver_id):
        """Get buses by driver"""
        buses = Bus.query.filter_by(driver_id=driver_id).all()

        if not buses:
            return {"message": "No buses found for this driver."}, 404

        return [
            {
                'id': bus.id,
                'username': bus.username,
                'cost_per_seat': bus.cost_per_seat,
                'number_of_seats': bus.number_of_seats,
                'route': bus.route,
                'travel_time': bus.travel_time.isoformat() if bus.travel_time else None,
                'number_plate': bus.number_plate,
                'image':bus.image,
                
            } for bus in buses
        ], 200


class ViewBusById(Resource):
    # @jwt_required()
    def get(self, bus_id):
        """View a bus by ID"""
        bus = Bus.query.filter_by(id=bus_id).first()

        if not bus:
            return {"message": "No buses found."}, 404

        return ({
            'id': bus.id,
            'username': bus.username,
            'cost_per_seat': bus.cost_per_seat,
            'number_of_seats': bus.number_of_seats,
            'route': bus.route,
            'travel_time': bus.travel_time.isoformat(),
            'number_plate': bus.number_plate,
            'image':bus.image
        }), 200


class ViewBusesByDriver(Resource):
    # @jwt_required()
    def get(self, driver_id):
        """Get buses by driver"""
        buses = Bus.query.filter_by(driver_id=driver_id).all()

        if not buses:
            return {"message": "No buses found for this driver."}, 404

        return [{
            'id': bus.id,
            'username': bus.username,
            'cost_per_seat': bus.cost_per_seat,
            'number_of_seats': bus.number_of_seats,
            'route': bus.route,
            'travel_time': bus.travel_time.isoformat() if bus.travel_time else None,
            'number_plate': bus.number_plate,
            'image':bus.image,
        } for bus in buses], 200



class DeleteBus(Resource):
    # @jwt_required()
    def delete(self, bus_id):
        """Delete a bus by ID"""
        bus = Bus.query.get(bus_id)
        if bus:
            db.session.delete(bus)
            db.session.commit()
            return ({'message': 'Bus deleted successfully'}), 200
        else:
            return ({'message': 'Bus not found'}), 404


#Scheduling Buses
class GetScheduledBuses(Resource):
    # @jwt_required()
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

class ScheduledBuses(Resource):
    # @jwt_required()
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

        # Parse input values
        try:
            departure_datetime = datetime.strptime(data.get('departure_time'), "%H:%M:%S")
            arrival_datetime = datetime.strptime(data.get('arrival_time'), "%H:%M:%S")
            travel_date = datetime.strptime(data.get('travel_date'), "%Y-%m-%d").date() 
        except ValueError as e:
            return {"error": "Invalid date or time format."}, 400

        try:
            new_schedule = Schedule(
                bus_id=data.get('bus_id'),
                departure_time=departure_datetime.time(),  
                arrival_time=arrival_datetime.time(), 
                travel_date=travel_date,
                available_seats=data.get('available_seats'),
                occupied_seats=data.get('occupied_seats')
            )
            db.session.add(new_schedule)
            db.session.commit()
            return {"message": "Scheduled bus created successfully.", "schedule_id": new_schedule.id}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to create scheduled bus.", "details": str(e)}, 500
        
class EditScheduledBuses(Resource):
    def patch(self, schedule_id):
        """Update an existing scheduled bus
        ---
        parameters:
          - name: schedule_id
            in: path
            required: true
            type: integer
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
          200:
            description: Scheduled bus updated successfully
          400:
            description: Error with missing fields or invalid data
          404:
            description: Scheduled bus not found
        """
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return {"error": "Scheduled bus not found."}, 404

        # Define required fields
        required_fields = ['bus_id', 'departure_time', 'arrival_time', 'travel_date', 'available_seats', 'occupied_seats']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {
                "warning": f"Missing fields: {', '.join(missing_fields)}. No changes made to these fields."
            }, 400

        try:
            # Update the fields if they are provided in the request
            if 'bus_id' in data:
                schedule.bus_id = data['bus_id']
            if 'departure_time' in data:
                schedule.departure_time = datetime.strptime(data['departure_time'], "%H:%M:%S").time()
            if 'arrival_time' in data:
                schedule.arrival_time = datetime.strptime(data['arrival_time'], "%H:%M:%S").time()
            if 'travel_date' in data:
                schedule.travel_date = datetime.strptime(data['travel_date'], "%Y-%m-%d").date()
            if 'available_seats' in data:
                schedule.available_seats = data['available_seats']
            if 'occupied_seats' in data:
                schedule.occupied_seats = data['occupied_seats']

            db.session.commit()
            return {"message": "Scheduled bus updated successfully."}, 200
        except ValueError:
            return {"error": "Invalid date or time format."}, 400
        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to update scheduled bus.", "details": str(e)}, 500

        
class DeleteSchedule(Resource):
    # @jwt_required()  # Protect this route if you want authentication
    def delete(self, schedule_id):
        # Fetch the schedule by ID
        schedule = Schedule.query.get(schedule_id)

        if not schedule:
            return ({"msg": "Schedule not found"}), 404

        # Delete the schedule
        db.session.delete(schedule)
        db.session.commit()

        return ({"msg": "Schedule deleted successfully"}), 200
    
class ViewCustomers(Resource):
    # @jwt_required()
    def get(self):
        """View all registered customers"""
        customers = Customer.query.all()
        
        customer_list = [{
            'id': customer.id,
            'firstname': customer.firstname,
            'lastname': customer.lastname,
            'email': customer.email,
        } for customer in customers]
        
        return {"customers": customer_list}, 200

#Bus Cost per Seat

class ViewBusCost(Resource):
    # @jwt_required()
    def get(self, bus_id):
        """Get the cost per seat of a bus
        ---
        parameters:
          - name: bus_id
            in: path
            required: true
            type: integer
        responses:
          200:
            description: Cost per seat retrieved successfully
          404:
            description: Bus not found
        """
        current_driver_id = get_jwt_identity()
        bus = Bus.query.filter_by(id=bus_id, driver_id=current_driver_id).first()

        if not bus:
            return {"error": "Bus not found."}, 404

        return {
            'cost_per_seat': bus.cost_per_seat,
           
        }, 200
    
class AddBusCostByID(Resource):
    # @jwt_required()
    def post(self, bus_id):
        """Add cost per seat for a specific bus by ID
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
          201:
            description: Bus cost created successfully
          404:
            description: Bus not found
          400:
            description: Error with missing fields or invalid data
        """
        current_driver_id = get_jwt_identity()

        # Check if the bus exists for the current driver
        bus = Bus.query.filter_by(id=bus_id, driver_id=current_driver_id).first()
        if not bus:
            return {"error": "Bus not found."}, 404

        data = request.get_json()

        if 'cost_per_seat' not in data:
            return {"error": "Missing required field: cost_per_seat"}, 400

        try:
            bus.cost_per_seat = float(data['cost_per_seat'])  # Update cost per seat
            db.session.commit()
            return {"message": "Cost per seat created successfully.", "bus_id": bus.id}, 201
        except ValueError as ve:
            return {"error": "Invalid data provided.", "details": str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to add bus cost per seat.", "details": str(e)}, 500

class UpdateBusCostByID(Resource):
    # @jwt_required()
    def put(self, bus_id):
        """Update the cost per seat of a specific bus by ID
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
          404:
            description: Bus not found
          400:
            description: Invalid data provided
        """
        current_driver_id = get_jwt_identity()
        bus = Bus.query.filter_by(id=bus_id, driver_id=current_driver_id).first()

        if not bus:
            return {"error": "Bus not found."}, 404

        data = request.get_json()
        if 'cost_per_seat' not in data:
            return {"error": "Missing required field: cost_per_seat"}, 400

        try:
            bus.cost_per_seat = float(data['cost_per_seat'])  # Update cost per seat
            db.session.commit()
            return {"message": "Cost per seat updated successfully."}, 200
        except ValueError as ve:
            return {"error": "Invalid data provided.", "details": str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to update bus cost.", "details": str(e)}, 500
        
class UpdateSeat(Resource):
    def put(self, seat_id):
        """Update a seat by ID."""
        data = request.get_json()
        bus_id = data.get('bus_id')  # Get bus_id from the request body

        # Validate bus_id
        if bus_id is None:
            return {"message": "bus_id is required."}, 400

        seat = Seat.query.get(seat_id)  # Retrieve the seat using seat_id from the route
        if not seat:
            return {"message": "Seat not found."}, 404

        seat.bus_id = bus_id  # Update the bus_id
        # Update other fields if necessary
        db.session.commit()

        return {"message": "Seat updated successfully."}, 200

    
class DeleteSeat(Resource):
    def delete(self, seat_id):
        """Delete a seat by ID.
        ---
        parameters:
          - name: seat_id
            in: path
            type: integer
            required: true
            description: The ID of the seat to delete
        responses:
          200:
            description: Seat successfully deleted
          404:
            description: Seat not found
        """
        # Query the database for the seat associated with the provided ID
        seat = Seat.query.get(seat_id)

        if not seat:
            return {"message": "Seat not found."}, 404

        # Delete the seat
        db.session.delete(seat)
        db.session.commit()

        return {"message": "Seat successfully deleted."}, 200


# Register the resources with the API
driver_api.add_resource(Signup, "/signup")
driver_api.add_resource(Login, "/login")
driver_api.add_resource(ProtectedResource, "/protected")
driver_api.add_resource(RegisterBuses, "/register/buses")
driver_api.add_resource(EditBuses, "/edit-buses/<int:bus_id>")
driver_api.add_resource(ViewBusesByDriver, '/buses/driver/<int:driver_id>')
driver_api.add_resource(ViewCustomers, '/customers')
driver_api.add_resource(ViewBusById, '/buses/<int:bus_id>')
driver_api.add_resource(DeleteBus, '/bus/<int:bus_id>', endpoint='delete_bus')
driver_api.add_resource(GetScheduledBuses, "/view_scheduled_buses")
driver_api.add_resource(ScheduledBuses, "/schedule_buses")
driver_api.add_resource(EditScheduledBuses, "/edit-scheduled_buses/<int:schedule_id>")
driver_api.add_resource(DeleteSchedule, "/delete_scheduled_buses/<int:schedule_id>")
driver_api.add_resource(UpdateSeat, "/update_seat")
driver_api.add_resource(DeleteSeat, "/delete_seat/<int:seat_id>")
driver_api.add_resource(ViewBusCost, '/buses/<int:bus_id>/cost', endpoint='get_bus_cost')
driver_api.add_resource(AddBusCostByID, '/buses/<int:bus_id>/cost', endpoint='add_bus_cost_by_id')
driver_api.add_resource(UpdateBusCostByID, '/buses/<int:bus_id>/cost', endpoint='update_bus_cost_by_id')
