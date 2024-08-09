from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Customer,Admin,Driver
from flask import jsonify
from app import app
# Role-checking decorator
def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            user = None
            if current_user['role'] == 'customer':
                user = Customer.query.get(current_user['id'])
            elif current_user['role'] == 'driver':
                user = Driver.query.get(current_user['id'])
            elif current_user['role'] == 'admin':
                user = Admin.query.get(current_user['id'])
            
            if user is None or user.role != required_role:
                return jsonify({"msg": "Access denied."}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Example usage in a route
@app.route('/admin-only', methods=['GET'])
@jwt_required()
@role_required('admin')
def admin_only_route():
    return jsonify({"msg": "Welcome, admin!"}), 200

@app.route('/driver-only', methods=['GET'])
@jwt_required()
@role_required('driver')
def driver_only_route():
    return jsonify({"msg": "Welcome, driver!"}), 200

@app.route('/customer-only', methods=['GET'])
@jwt_required()
@role_required('customer')
def customer_only_route():
    return jsonify({"msg": "Welcome, customer!"}), 200
