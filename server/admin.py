from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api, Resource
from .models import Admin, db, Driver, Customer, Bus, Schedule
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_bcrypt import Bcrypt
from functools import wraps

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')
api = Api(admin_bp)
bcrypt = Bcrypt()

class Signup(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"error": "No input data provided"}, 400

        username = data['username']
        email = data['email']
        password = data['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        admin = Admin(username=username, email=email, password=hashed_password)
        db.session.add(admin)
        db.session.commit()

        return {"message": "Admin created successfully"}, 201

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        email = data['email']
        password = data['password']

        admin = Admin.query.filter_by(username=username, email=email).first()

        if admin and bcrypt.check_password_hash(admin.password, password):
            access_token = create_access_token(identity=admin.id, additional_claims={"role":admin.role})
            return {"access_token":access_token}, 200
        else:
            return {"error": "Invalid credentials"}, 401
        
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt_identity()
        if claims["role"] != "admin":
            return {"error": "Admin-only access"}, 403
        return fn(*args, **kwargs)
    return jwt_required(wrapper)

class Drivers(Resource):
    @admin_required
    def get(self):
        drivers=Driver.query.all()
        if not drivers:
            return jsonify({"message": "No buses found."}), 404
        return jsonify([{
                'id': driver.id,
                'firstname': driver.firstname,
                'lastname': driver.lastname,
                'license_number': driver.license_number,
                'experiene_years': driver.experiene_years,
                'phone_number': driver.phone_number, 
                'email': driver.email,
                'password': driver.password,
            } for driver in drivers]),200
    
    @admin_required
    def delete(self, id):
        driver_record = Driver.query.filter_by(id=id).first()
        db.session.delete(driver_record)
        db.session.commit()
        response_dict = {
            "message": "Driver deleted successfully",
            "driver_id": driver_record.id
        }
        response = make_response(response_dict, 200)
        return response
    
class Customers(Resource):
    @admin_required
    def get(self):
        response_dict_list = [customer.to_dict() for customer in Customer.query.all()]
        return response_dict_list, 200

class Buses(Resource):
    @admin_required
    def get(self):
        response_dict_list = [bus.to_dict() for bus in Bus.query.all()]
        return jsonify(response_dict_list), 200
    
class Schedules(Resource):
    @admin_required
    def get(self):
        response_dict_list = [scheduled_bus.to_dict() for scheduled_bus in Schedule.query.all()]
        return jsonify(response_dict_list), 200

api.add_resource(Signup, '/signup')    
api.add_resource(Login, '/login')
api.add_resource(Drivers, '/drivers', "/drivers/<int:id>")
api.add_resource(Customers, '/customers')
api.add_resource(Buses, '/buses')
api.add_resource(Schedules, '/scheduled_buses')