import random
from flask_jwt_extended import create_access_token,JWTManager
from flask_cors import CORS
from .customers import customer_bp,bcrypt,bcrypt as customer_bcrypt
from .driver import driver_bp,bcrypt as driver_bcrypt
from datetime import timedelta,date,datetime
from flask import Flask,jsonify,request
from flask_migrate import Migrate
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()

from .models import db,Bus,Schedule,Customer,Admin,Driver,Booking

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URI')
# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///bus_booking.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "fsbdgfnhgvjnvhmvh"+str(
    random.randint(1,1000000000000))
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["SECRET_KEY"] = "JKSRVHJVFBSRDFV"+str(random.randint(1,1000000000000))
app.json.compact = False



migrate = Migrate(app, db)
db.init_app(app)
customer_bcrypt.init_app(app)  
driver_bcrypt.init_app(app)
jwt=JWTManager

# Register blueprints
app.register_blueprint(customer_bp)
app.register_blueprint(driver_bp)  


#Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Customer.query.filter_by(email=data['email']).first() or \
           Driver.query.filter_by(email=data['email']).first() or \
           Admin.query.filter_by(email=data['email']).first()

    if user and user.password == data['password']:
        access_token = create_access_token(identity={"id": user.id, "role": user.role})
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad email or password"}), 401

#home
@app.route("/")
def home():
    return {"msg":"event"}

#Customers
@app.route('/customers', methods=['GET'],endpoint='view_customers')
def get_buses():
    customers=Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers]),200

@app.route('/customers',methods=['POST'],endpoint='adding_customers')
def add_customers():
    data=request.get_json()

    required_fields=['firstname','lastname','email','password','address','phone_number','id_or_passport']

    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}),400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_customer=Customer(firstname=data['firstname'],
                lastname=data['lastname'],
                email=data['email'],
                password=hashed_password,
                address=data['address'],
                phone_number=data['phone_number'],
                id_or_passport=data['id_or_passport']
                # role=data['role']
    )
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({'message': 'Customer created successfully'}), 201

@app.route('/customer/<int:customer_id>',methods=['DELETE'],endpoint='delete_customer')
def delete_customer(customer_id):
    customer=Customer.query.get(customer_id)

    if customer:
        db.session.delete(customer)
        db.session.commit()

        return jsonify({'message': 'Customer deleted successfully'}),200
    
    else:
        return jsonify({'message': 'Customer not found'}), 404
    

#Bookings
@app.route('/bookings', methods=['GET'],endpoint='view_bookings')
def get_bookings():
    bookings=Booking.query.all()
    return jsonify([booking.to_dict() for booking in bookings]),200

#Buses
@app.route('/buses', methods=['GET'],endpoint='view_buses')
def get_buses():
    buses=Bus.query.all()
    return jsonify([bus.to_dict() for bus in buses]),200

@app.route('/buses', methods=['POST'], endpoint='add_bus_on_availability')
def add_buses():
    data=request.get_json()

    required_fields=['username','cost_per_seat','number_of_seats','route','travel_time','number_plate']
   
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
@app.route('/scheduled_bus',methods=['GET'], endpoint='scheduled_bus')
def get_scheduled_bus():
    scheduled_buses=Schedule.query.all()
    return jsonify([scheduled_bus.to_dict() for scheduled_bus in scheduled_buses]),200



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
    



if __name__ == "__main__":
    app.run(port=5555, debug=True)