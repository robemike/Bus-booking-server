import random
from flask_jwt_extended import JWTManager,get_jwt,jwt_required
from flask_cors import CORS
from .customers import customer_bp,bcrypt as customer_bcrypt
from .driver import driver_bp,bcrypt as driver_bcrypt
from datetime import timedelta,date,datetime
from flask import Flask,jsonify,request
from flask_migrate import Migrate
# from mpesa import mpesa_client
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()
from flask_swagger_ui import get_swaggerui_blueprint
from .models import db,Bus,Schedule,Customer,Booking,Driver



app = Flask(__name__)
SWAGGER_URL = '/swagger/'  
API_URL = '/static/swagger.json' 


# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  
    API_URL,
    config={  
        'app_name': "Test application"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/swagger/', strict_slashes=False)
def swagger_view():
    return app.send_static_file('swagger.json')
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URI')
# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///bus_booking.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "fsbdgfnhgvjnvhmvh"+str(
    random.randint(1,1000000000000))
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["SECRET_KEY"] = "JKSRVHJVFBSRDFV"+str(random.randint(1,1000000000000))
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"] 
app.json.compact = False
jwt = JWTManager(app)

# Logout
BLACKLIST = set()
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, decrypted_token):
    return decrypted_token['jti'] in BLACKLIST

@app.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    jti = get_jwt()["jti"]
    BLACKLIST.add(jti)
    return jsonify({"success":"Successfully logged out"}), 200




migrate = Migrate(app, db)
db.init_app(app)
customer_bcrypt.init_app(app)  
driver_bcrypt.init_app(app)
jwt = JWTManager(app)


# Register blueprints
app.register_blueprint(customer_bp)
app.register_blueprint(driver_bp)  


#Routes
# @app.route('/stk_push', methods=['GET'])
# def stk_push():
#     # Retrieve parameters from the request
#     phone_number = request.args.get('phone_number') 
#     if not phone_number:
#         return jsonify({"error": "Phone number is required"}), 400

#     amount = request.args.get('amount', 1, type=int)
#     account_reference = 'Laurine'
#     transaction_desc = 'Description'
#     callback_url = 'https://api.darajambili.com/express-payment'
    
#     try:
#         response = mpesa_client.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
#         return jsonify(response), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
#home
@app.route("/")
def home():
    return {"msg":"Welcome to Bus Booking App"}

#Customers
@app.route('/customers', methods=['GET'],endpoint='view_customers')
def get_buses():
    customers=Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers]),200


#Get Drivers
@app.route('/drivers', methods=['GET'], endpoint='view_drivers')
def get_scheduled_bus():
    drivers = Driver.query.all()
    if not drivers:
        return jsonify({"message": "No Driver found."}), 404
    return jsonify([{
                'id': driver.id,
                'firstname': driver.firstname,
                'lastname': driver.lastname,
                'license_number': driver.license_number,
                'experience_years': driver.experience_years,
                'phone_number': driver.phone_number,
                'email':driver.email
            } for driver in drivers]), 200


@app.route('/drivers/<int:driver_id>', methods=['GET'])
def get_driver(driver_id):
    driver = Driver.query.get(driver_id)
    
    if not driver:
        return {"message": "Driver not found."}, 404
    return jsonify({
        'id': driver.id,
        'firstname': driver.firstname,
        'lastname': driver.lastname,
        'license_number': driver.license_number,
        'experience_years': driver.experience_years,
        'phone_number': driver.phone_number,
        'email': driver.email
    }), 200


#Buses
@app.route('/buses', methods=['GET'], endpoint='view_buses')
def get_buses():
    buses = Bus.query.all()
    if not buses:
        return jsonify({"message": "No buses found."}), 404

    return jsonify([{
        'id': bus.id,
        'username': bus.username,
        'cost_per_seat': bus.cost_per_seat,
        'number_of_seats': bus.number_of_seats,
        'route': bus.route,
        'travel_time': bus.travel_time.isoformat(), 
        'number_plate': bus.number_plate,
    } for bus in buses]), 200


# Get buses by driver
@app.route('/buses/driver/<int:driver_id>', methods=['GET'])
def get_buses_by_driver(driver_id):
    buses = Bus.query.filter_by(driver_id=driver_id).all()
    
    if not buses:
        return jsonify({"message": "No buses found for this driver."}), 404

    return jsonify([{
        'id': bus.id,
        'username': bus.username,
        'cost_per_seat': bus.cost_per_seat,
        'number_of_seats': bus.number_of_seats,
        'route': bus.route,
        'travel_time': bus.travel_time.isoformat() if bus.travel_time else None,
        'number_plate': bus.number_plate
    } for bus in buses]), 200  # Added status code 200


@app.route('/buses', methods=['POST'], endpoint='add_bus_on_availability')
def add_buses():
    data=request.get_json()

    required_fields=['username','cost_per_seat','number_of_seats','route','travel_time','number_plate','driver_id']
   
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}),400

    new_bus=Bus(username=data['username'],
                driver_id=data['driver_id'],
                cost_per_seat=data['cost_per_seat'],
                number_of_seats=data['number_of_seats'],
                route=data['route'],
                travel_time=data['travel_time'],
                number_plate=data['number_plate']
    )
    db.session.add(new_bus)
    db.session.commit()

    return jsonify({'message': 'Bus created successfully'}), 201

@app.route('/bus/<int:bus_id>',methods=['DELETE'],endpoint='delete_bus')
def delete_buses(bus_id):
    bus=Bus.query.get(bus_id)
    if bus:
        db.session.delete(bus)
        db.session.commit()
        return jsonify({'message': 'Bus deleted successfully'}), 200
       
    else:
        return jsonify({'message': 'Bus not found'}), 404


#Scheduled Bus
@app.route('/scheduled_bus', methods=['GET'], endpoint='view_scheduled_bus')
def get_scheduled_bus():
    scheduled_buses = Schedule.query.all()
    if not scheduled_buses:
        return jsonify({"message": "No scheduled buses found."}), 404

    return jsonify([{
        'id': scheduled_bus.id,
        'bus_id': scheduled_bus.bus_id,
        'departure_time': scheduled_bus.departure_time.isoformat() if scheduled_bus.departure_time else None,
        'arrival_time': scheduled_bus.arrival_time.isoformat() if scheduled_bus.arrival_time else None,
        'travel_date': scheduled_bus.travel_date.isoformat() if scheduled_bus.travel_date else None,
        'available_seats': scheduled_bus.available_seats,
        'occupied_seats': scheduled_bus.occupied_seats
    
    } for scheduled_bus in scheduled_buses]), 200



@app.route('/scheduled_bus', methods=['POST'], endpoint='add_scheduled_bus')
def create_schedule_buses():
    data = request.get_json()

    required_fields = ['departure_time', 'arrival_time', 'travel_date', 'available_seats', 'occupied_seats']

    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

   
    try:
        travel_date = datetime.strptime(data['travel_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid travel_date format, expected YYYY-MM-DD'}), 400

    
    try:
        departure_time = datetime.combine(travel_date, datetime.strptime(data['departure_time'], '%H:%M:%S').time())
        arrival_time = datetime.combine(travel_date, datetime.strptime(data['arrival_time'], '%H:%M:%S').time())
    except ValueError:
        return jsonify({'message': 'Invalid time format, expected HH:MM:SS'}), 400

    new_schedule = Schedule(
        departure_time=departure_time,  
        arrival_time=arrival_time,       
        travel_date=travel_date,          
        available_seats=data['available_seats'],
        occupied_seats=data['occupied_seats'],
        bus_id=data['bus_id']
    )

    db.session.add(new_schedule)
    db.session.commit()

    return jsonify({'message': 'Scheduled Bus created successfully'}), 201

@app.route('/scheduled_bus/<int:bus_id>', methods=['PUT'], endpoint='updated_schedule')
def update_schedule(bus_id):
    data = request.get_json()
    scheduled_buses = Schedule.query.get(bus_id)
    if  scheduled_buses:
        scheduled_buses.depature_time = data['depature_time']
        scheduled_buses.arrival_time = data['arrival_time']
        scheduled_buses.travel_date =  data['travel_date']
        scheduled_buses.available_seats =  data['available_seats']
        scheduled_buses.occupied_seats =  data['occupied_seats']

        if 'travel_date' in data:
            scheduled_buses.travel_date = date.fromisoformat(data['travel_date'])
        else:
            scheduled_buses.travel_date = None

        db.session.commit()
        return jsonify({'message': 'Schedule updated successfully'}), 200
    else:
        return jsonify({'message': 'Schedule not found'}), 404
    
#Tickets

@app.route('/tickets', methods=['GET'],endpoint='view_tickets')
def get_tickets():
    tickets=Booking.query.all()
    return jsonify([{
            'id': ticket.id,
            'username': ticket.username,
            'booking_date': ticket.booking_date,
            'number_of_seats': ticket.number_of_seats,
            'route': ticket.route,
            'total_cost':ticket.total_cost
            
        } for ticket in tickets]),200

@app.route('/tickets/<int:ticket_id>', methods=['GET'], endpoint='view_tickets_by_id')
def get_ticket_by_id(ticket_id):
    # Fetch the ticket based on the provided ticket_id
    ticket = Booking.query.get(ticket_id)
    
    if not ticket:
        return jsonify({"message": "No ticket found for this ID."}), 404
    
    return jsonify({
        'id': ticket.id,
        'username': ticket.username,
        'booking_date': ticket.booking_date.isoformat(),  # Ensure this is formatted correctly
        'number_of_seats': ticket.number_of_seats,
        'route': ticket.route,
        'total_cost': ticket.total_cost
    }), 200



if __name__ == "__main__":
    app.run(port=5555, debug=True)