from flask import Blueprint, request,make_response
from flask_restful import Api, Resource
from .models import Admin, Driver, Customer, Bus, Schedule
from .config import bcrypt,db
from flask_jwt_extended import create_access_token,create_refresh_token,get_jwt_identity,jwt_required,current_user



admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')
api = Api(admin_bp)

class AdminSignup(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided."}, 400

        required_fields = ["username", "email", "password"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]

        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400

        email = data["email"]

        # Check if an admin already exists
        if Admin.query.first():
            return {"error": "An admin already exists."}, 400

        try:
            hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
            new_admin = Admin(
                username=data["username"],
                email=email,
                password=hashed_password
            )
            db.session.add(new_admin)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

        return {"success": "Admin registered successfully"}, 201

class AdminLogin(Resource):
    def post(self):
        """Admin login"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {"error": "Username and password are required."}, 400

        admin = Admin.query.filter_by(username=username).first()
        if admin:
            is_valid = bcrypt.check_password_hash(admin.password, password)
            print(f"Password match: {is_valid}")

            if is_valid:
                access_token = create_access_token(identity=admin.id)
                refresh_token = create_refresh_token(identity=admin.id)
                
                # Serialize the admin object to avoid JSON serialization errors
                admin_data = {
                    "id": admin.id,
                    "username": admin.username,
                    # Add other necessary fields from the admin object
                }

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "admin": admin_data
                }, 200

        # If credentials are invalid
        return {"error": "Invalid Admin credentials"}, 401


class ViewDriverBuses(Resource):
    def get(self):
        """Fetch all buses registered by the driver"""
        driver_id = get_jwt_identity() 

        buses = Bus.query.filter_by(driver_id=driver_id).all()
        return [{
            'id': bus.id,
            'number_plate': bus.number_plate,
            'cost_per_seat': bus.cost_per_seat,
            'number_of_seats': bus.number_of_seats,
            'route': bus.route
        } for bus in buses], 200

class AddDriver(Resource):
    def post(self):
        """Add a new driver"""
        data = request.get_json()
        required_fields = ["firstname", "lastname", "license_number", "experience_years", "phone_number", "email", "password"]
        missing_fields = [field for field in required_fields if field not in data or not str(data[field])] 

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        existing_driver = Driver.query.filter_by(email=data["email"], license_number=data["license_number"]).first()
        if existing_driver:
            return {"error": "Driver already exists."}, 400

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        new_driver = Driver(
            firstname=data["firstname"],
            lastname=data["lastname"],
            email=data["email"],
            password=hashed_password,
            license_number=data["license_number"],
            experience_years=data["experience_years"],
            phone_number = str(data["phone_number"])

        )
        db.session.add(new_driver)
        db.session.commit()
        return {"message": "Driver added successfully."}, 201

# class DeleteDriver(Resource):
#     def delete(self, driver_id):
#         """Delete a driver"""
#         driver = Driver.query.get(driver_id)
#         if not driver:
#             return {"error": "Driver not found."}, 404

#         db.session.delete(driver)
#         db.session.commit()
#         return {"message": "Driver deleted successfully."}, 200

class ViewCustomers(Resource):
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


class ViewScheduledBuses(Resource):
    def get(self):
        """View all scheduled buses"""
        try:
            scheduled_buses = Schedule.query.all()
            
            # Log the number of scheduled buses found
            print(f"Number of scheduled buses found: {len(scheduled_buses)}")
            
           
            scheduled_buses_list = [{
                'id': scheduled_bus.id,
                'bus_id': scheduled_bus.bus_id,
                'departure_time': scheduled_bus.departure_time.isoformat(),
                'arrival_time': scheduled_bus.arrival_time.isoformat(),
                'travel_date': scheduled_bus.travel_date.isoformat(),
                'available_seats': scheduled_bus.available_seats,
                'occupied_seats': scheduled_bus.occupied_seats,
            } for scheduled_bus in scheduled_buses]

            return {"scheduled_buses": scheduled_buses_list}, 200
        except Exception as e:
            return {"error": str(e)}, 500

class ViewDrivers(Resource):
    def get(self):
        """Get all drivers
        ---
        responses:
          200:
            description: A list of drivers
          403:
            description: User is not an admin
        """
        # current_user_id = get_jwt_identity()  # Get the current user's identity

        # Check if the current user is an admin by querying the Admin model
        # admin_user = Admin.query.get(current_user_id) 
        # if not admin_user:
        #     return {"error": "User is not an admin"}, 403

        drivers = Driver.query.all()  
        if not drivers:
            return {"message": "No drivers found."}, 404

        return [{
            'id': driver.id,
            'firstname': driver.firstname,  
            'lastname': driver.lastname,
            'license_number': driver.license_number,  
            'phone_number': driver.phone_number,  
            'email': driver.email, 
            'experience_years': driver.experience_years
        } for driver in drivers], 200
    
class ViewDriversByID(Resource):
    def get(self, driver_id):
        """Get driver by ID
        ---
        parameters:
          - name: driver_id
            in: path
            required: true
            type: integer
        responses:
          200:
            description: Driver details
          404:
            description: Driver not found
          403:
            description: User is not an admin
        """
        current_user_id = get_jwt_identity()  # Get the current user's identity

        # Check if the current user is an admin
        admin_user = Admin.query.get(current_user_id) 
        if not admin_user:
            return {"error": "User is not an admin"}, 403

        driver = Driver.query.get(driver_id)  # Retrieve the driver by ID
        if not driver:
            return {"message": "Driver not found."}, 404

        return {
            'id': driver.id,
            'firstname': driver.firstname,  
            'lastname': driver.lastname,
            'license_number': driver.license_number,  
            'phone_number': driver.phone_number,  
            'email': driver.email, 
            'experience_years': driver.experience_years
        }, 200

class ViewBuses(Resource):
    def get(self):
        """Get all buses
        ---
        responses:
          200:
            description: A list of buses
          404:
            description: No buses found
        """
        buses = Bus.query.all()
        if not buses:
            return {"message": "No buses found."}, 404

        # return [{
        #     'id': bus.id,
        #     'username': bus.username,
        #     'cost_per_seat': bus.cost_per_seat,
        #     'number_of_seats': bus.number_of_seats,
        #     'route': bus.route,
        #     'travel_time': bus.travel_time.isoformat(), 
        #     'number_plate': bus.number_plate,
        #     'image':bus.image,
        #     'seats':bus.seats
        # } for bus in buses], 200
        return make_response([bus.to_dict() for bus in buses],200)
    

class ViewBusesByID(Resource):
    def get(self, bus_id):
        """Get bus by ID
        ---
        parameters:
          - name: bus_id
            in: path
            required: true
            type: integer
        responses:
          200:
            description: Bus details
          404:
            description: Bus not found
        """
        bus = Bus.query.filter_by(id=bus_id).first()  
        if not bus:
            return {"message": "No buses found."}, 404

        return {
            'id': bus.id,
            'username': bus.username,
            'cost_per_seat': bus.cost_per_seat,
            'number_of_seats': bus.number_of_seats,
            'route': bus.route,
            'travel_time': bus.travel_time.isoformat(),
            'number_plate': bus.number_plate,
        }, 200

    
    
# class DeleteAdmin(Resource):
#     def delete(self, admin_id):
#         """Delete an admin by ID"""
#         admin = Admin.query.get(admin_id)
#         if not admin:
#             return {"error": "Admin not found."}, 404

#         db.session.delete(admin)
#         db.session.commit()
#         return {"message": "Admin deleted successfully."}, 200


# # Register the new resource with the API
# api.add_resource(DeleteAdmin, '/<int:admin_id>')




# Register the resources with the API

api.add_resource(AdminSignup, '/signup')
api.add_resource(AdminLogin, '/login')
api.add_resource(ViewDrivers, '/view_drivers')
api.add_resource(ViewDriversByID, '/drivers/<int:driver_id>', endpoint='view_driver_by_id')
api.add_resource(ViewDriverBuses, '/driver/buses')
api.add_resource(AddDriver, '/drivers')
# api.add_resource(DeleteDriver, '/drivers/<int:driver_id>')
api.add_resource(ViewCustomers, '/customers')
api.add_resource(ViewBuses, '/buses')
api.add_resource(ViewBusesByID, '/buses/<int:bus_id>', endpoint='view_buses_by_id')
api.add_resource(ViewScheduledBuses, '/scheduled_buses')