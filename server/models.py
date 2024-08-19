from datetime import datetime,date
from sqlalchemy_serializer import SerializerMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates, relationship
from .config import db


class Customer(db.Model, SerializerMixin):
    _tablename_ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    id_or_passport = db.Column(db.String, unique=True, nullable=False)
    role=db.Column(db.String,default='customer')
   

    bookings = db.relationship("Booking", back_populates="customer")

    @validates("email")
    def validate_email(self, key, email):
        if "@" not in email:
            raise ValueError("Invalid email Format")
        return email

    @validates("phone_number")
    def validate_phone_number(self, key, phone_number):
        if len(phone_number) != 10 or not phone_number.isdigit():
            raise ValueError("Phone number must be exactly 10 digits and numeric")
        
        if Driver.query.filter_by(phone_number=phone_number).first():
            raise ValueError("Phone number must be unique")
        
        return phone_number

    @validates("id_or_passport")
    def validate_id_or_passport(self, key, id_or_passport):
        if len(id_or_passport) != 8 or not id_or_passport.isdigit():
            raise ValueError("ID or Passport must be exactly 8 digits and numeric")
        return id_or_passport
    

class Bus(db.Model, SerializerMixin):
    _tablename_ = "buses"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"))
    cost_per_seat = db.Column(db.Integer, nullable=False)
    number_of_seats = db.Column(db.Integer, nullable=False)
    route = db.Column(db.String, nullable=False)
    travel_time = db.Column(db.Time, nullable=False)
    number_plate = db.Column(db.String,unique=True)
    image = db.Column(db.String) 
    driver = db.relationship('Driver', back_populates='buses')

    
    
    driver = relationship("Driver", back_populates="buses",lazy='select')
    schedules = relationship("Schedule", back_populates="bus")
    bookings = relationship("Booking", back_populates="bus")
    seats =relationship("Seat", back_populates="bus")
   
    serialize_only = ('id', 'username', 'cost_per_seat', 'number_of_seats', 'route', 'travel_time', 'number_plate', 'image','seats')

    @validates("number_plate")
    def validate_number_plate(self, key, number_plate):
        if len(number_plate) != 8 :
            ValueError("Invalid number plate format")

        return number_plate


class Schedule(db.Model, SerializerMixin):
    _tablename_ = "schedules"
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey("buses.id"), nullable=False)
    departure_time = db.Column(db.Time, nullable=False)
    arrival_time = db.Column(db.Time, nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    occupied_seats = db.Column(db.Integer, nullable=False,default=0)

    serialize_only = ('id', 'bus_id', 'departure_time', 'arrival_time', 'travel_date', 'available_seats', 'occupied_seats')

    bus = db.relationship("Bus", back_populates="schedules")

    @validates("arrival_time")
    def validate_arrival_time(self, key, arrival_time):
        if arrival_time <= self.departure_time:
            raise ValueError("Arrival time must be after departure time")
        return arrival_time
    
    @validates('travel_date')
    def validate_travel_date(self, key, travel_date):
        """Validate that travel_date is not in the past."""
        # Convert string to date if necessary
        if isinstance(travel_date, str):
            travel_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
        
        if travel_date < date.today():
            raise ValueError("Travel date cannot be in the past.")
        return travel_date
    
    def validate_time_format(time_string):
        try:
            
            datetime.fromisoformat(time_string)
            return True
        except ValueError:
            return False


class Booking(db.Model, SerializerMixin):
    _tablename_ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey("buses.id"), nullable=False)
    booking_date = db.Column(db.Date, default=date.today)
    number_of_seats = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Float)
    selected_seats = db.Column(db.String) 
    destination = db.Column(db.String, nullable=False) 
    departure_time = db.Column(db.Time, nullable=False)
    current_address=db.Column(db.String, nullable=False)
    

    customer = db.relationship("Customer", back_populates="bookings")
    bus = db.relationship("Bus", back_populates="bookings")
    seats=db.relationship("Seat", back_populates="bookings")


    serialize_only = ('id', 'customer_id', 'bus_id', 'booking_date', 'number_of_seats','total_cost', 'selected_seats', 'destination', 'departure_time','current_address')


    @property
    def calculate_total_cost(self):
        if self.bus:
            return self.bus.cost_per_seat * self.number_of_seats
        return 0.0

    def save(self):
        self.total_cost = self.calculate_total_cost  
        db.session.add(self)
        db.session.commit()

    
class Seat(db.Model,SerializerMixin):
    _tablename_="seats"

    id = db.Column(db.Integer, primary_key=True)
    status=db.Column(db.String, default='available')
    seat_number=db.Column(db.String)
    bus_id=db.Column(db.Integer,db.ForeignKey('buses.id'), nullable=False)
    booking_id=db.Column(db.Integer,db.ForeignKey('bookings.id'))

    bus=db.relationship("Bus",back_populates="seats")
    bookings=db.relationship("Booking",back_populates="seats")

    serialize_rules = ('-bus','-bookings')


class Driver(db.Model, SerializerMixin):
    _tablename_ = "drivers"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    license_number = db.Column(db.String, nullable=False)  
    experience_years = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role=db.Column(db.String,default='driver')
    

    buses = db.relationship("Bus", back_populates="driver",lazy='dynamic')


    @validates("license_number")
    def validate_license_number(self, key, license_number):
        if len(license_number) != 8 :
            raise ValueError("License number must be exactly 8 digits")
        
        if Driver.query.filter_by(license_number=license_number).first():
            raise ValueError("License number must be unique")
        
        return license_number

    @validates("phone_number")
    def validate_phone_number(self, key, phone_number):
        if len(phone_number) != 10 or not phone_number.isdigit():
            raise ValueError("Phone number must be exactly 10 digits and numeric")
        
        if Driver.query.filter_by(phone_number=phone_number).first():
            raise ValueError("Phone number must be unique")
        
        return phone_number

    @validates("email")
    def validate_email(self, key, email):
        if "@" not in email:
            raise ValueError("Invalid email Format")
        elif Driver.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
        return email


class Admin(db.Model, SerializerMixin):
    _tablename_ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password= db.Column(db.String, nullable=False)
    role=db.Column(db.String,default='admin')