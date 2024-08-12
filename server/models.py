from datetime import datetime,date
from sqlalchemy_serializer import SerializerMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates, relationship

db = SQLAlchemy()


class Customer(db.Model, SerializerMixin):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    id_or_passport = db.Column(db.String, unique=True, nullable=False)
   

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
    __tablename__ = "buses"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    cost_per_seat = db.Column(db.Integer, nullable=False)
    number_of_seats = db.Column(db.Integer, nullable=False)
    route = db.Column(db.String, nullable=False)
    travel_time = db.Column(db.Time, nullable=False)
    number_plate = db.Column(db.String,unique=True)
    image = db.Column(db.String) 
    driver = db.relationship('Driver', backref='buses')
    
    

    driver = relationship("Driver", back_populates="buses",lazy='select')
    schedules = relationship("Schedule", back_populates="bus")
    bookings = relationship("Booking", back_populates="bus")
   

    @validates("number_plate")
    def validate_number_plate(self, key, number_plate):
        if len(number_plate) != 7 :
            ValueError("Invalid number plate format")


class Schedule(db.Model, SerializerMixin):
    __tablename__ = "schedules"
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey("buses.id"), nullable=False)
    departure_time = db.Column(db.Time, nullable=False)
    arrival_time = db.Column(db.Time, nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    occupied_seats = db.Column(db.Integer, nullable=False)


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
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey("buses.id"), nullable=False)
    booking_date = db.Column(db.Date, default=datetime.utcnow)
    number_of_seats = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Float)
    destination = db.Column(db.String, nullable=False) 
    departure_time = db.Column(db.Time, nullable=False)
    current_address=db.Column(db.String, nullable=False)
    

    customer = db.relationship("Customer", back_populates="bookings")
    bus = db.relationship("Bus", back_populates="bookings")


    @property
    def calculate_total_cost(self):
        if self.bus:
            return self.bus.cost_per_seat * self.number_of_seats
        return 0.0

    def save(self):
        self.total_cost = self.calculate_total_cost  
        db.session.add(self)
        db.session.commit()

class Driver(db.Model, SerializerMixin):
    __tablename__ = "drivers"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    license_number = db.Column(db.String, nullable=False)  
    experience_years = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    

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
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password= db.Column(db.String, nullable=False)
  