import random
from flask_jwt_extended import JWTManager,get_jwt,jwt_required
from flask_cors import CORS
from customers import customer_bp,bcrypt as customer_bcrypt
from driver import driver_bp,bcrypt as driver_bcrypt
from admin import admin_bp,bcrypt as admin_bcrypt
from models import db,Bus,Customer,Booking
from datetime import timedelta,date
from flask import Flask,jsonify,request
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import date,time
import os
from dotenv import load_dotenv
load_dotenv()
from flask_swagger_ui import get_swaggerui_blueprint
from flask_restful import Api


app = Flask(__name__)
CORS(app)

#Swagger
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
driver_api = Api(driver_bp)
bcrypt = Bcrypt(app)


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


@app.errorhandler(Exception)
def handle_exception(e):
    response = {
        "error": str(e)
    }
    return jsonify(response), 500


migrate = Migrate(app, db)
db.init_app(app)
customer_bcrypt.init_app(app)  
driver_bcrypt.init_app(app)


jwt = JWTManager(app)


# Register blueprints
app.register_blueprint(customer_bp)
app.register_blueprint(driver_bp)  
app.register_blueprint(admin_bp)


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
        # return jsonify({"error": str(e)}), 500
    
#home
@app.route("/")
def home():
    return {"msg":"Welcome to Bus Booking App"}

#Customers
@app.route('/customers', methods=['GET'],endpoint='view_customers')
def get_buses():
    customers=Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers]),200




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
        'image':bus.image
    } for bus in buses]), 200


    
#Tickets
@app.route('/tickets', methods=['GET'], endpoint='view_tickets')
def get_tickets():
    tickets = Booking.query.all()
    
    # Check if there are no tickets
    if not tickets:
        return {"message": "No tickets found."}, 404

    # Prepare the response
    ticket_list = [{
            'id': ticket.id,
            'booking_date': ticket.booking_date.isoformat(),  # Convert to ISO format
            'number_of_seats': ticket.number_of_seats,
            'selected_seats': ticket.selected_seats,
            'total_cost': ticket.total_cost,
            'destination': ticket.destination,
            'departure_time': ticket.departure_time.strftime("%H:%M:%S"),  # Format time
        } for ticket in tickets]

    return ticket_list, 200  # Return the list directly




@app.route('/tickets/<int:ticket_id>', methods=['GET'], endpoint='view_tickets_by_id')
def get_ticket_by_id(ticket_id):
  
  
    ticket = Booking.query.get(ticket_id)
    
    if not ticket:
        return ({"message": "No ticket found for this ID."}), 404
    
    return ({

            'id': ticket.id,
            'booking_date': ticket.booking_date,
            'number_of_seats': ticket.number_of_seats,
            'total_cost':ticket.total_cost,
            'selected_seats':ticket.selected_seats,
            'destination':ticket.destination,
            'departure_time': ticket.departure_time, 
    }), 200

 
@app.route('/tickets', methods=['POST'], endpoint='create_ticket')
# @jwt_required()  
def create_ticket():
    data = request.get_json() 

    # Validate input data
    if not data:
        return {"msg": "Missing input data"}, 400

    required_fields = ['customer_id', 'bus_id', 'booking_date', 'number_of_seats', 'selected_seats', 'total_cost', 'destination', 'departure_time', 'current_address']
    for field in required_fields:
        if field not in data:
            return {"msg": f"'{field}' is required"}, 400

    # Create a new Booking instance
    new_ticket = Booking(
        customer_id=data['customer_id'],
        bus_id=data['bus_id'],
        booking_date=data['booking_date'],  # Ensure this is a valid date string
        number_of_seats=data['number_of_seats'],
        selected_seats=data['selected_seats'],
        total_cost=data['total_cost'],
        destination=data['destination'],
        departure_time=data['departure_time'],  # Ensure this is a valid time string
        current_address=data['current_address']  
    )

    # Add to the session and commit to the database
    db.session.add(new_ticket)
    db.session.commit()

    # Convert times to strings for JSON serialization
    return {
        'msg': 'Ticket created successfully',
        'ticket': {
            'id': new_ticket.id,
            'customer_id': new_ticket.customer_id,
            'bus_id': new_ticket.bus_id,
            'booking_date': new_ticket.booking_date.isoformat(),  # Convert to ISO format string
            'number_of_seats': new_ticket.number_of_seats,
            'selected_seats': new_ticket.selected_seats,
            'total_cost': new_ticket.total_cost,
            'destination': new_ticket.destination,
            'departure_time': new_ticket.departure_time.strftime("%H:%M:%S"),  # Convert time to string
            'current_address': new_ticket.current_address  
        }
    }, 201  # Return the response with status code 201




if __name__ == "__main__":
    app.run(port=5555, debug=True)