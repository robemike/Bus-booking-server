from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

db = SQLAlchemy()


class Customer(db.Model,SerializerMixin):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    Firstname = db.Column(db.String, nullable=False)
    Lastname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    ID_or_Passport = db.Column(db.Integer, unique=True, nullable=False)

    bookings = relationship("Booking", back_populates="customer")


class Bus(db.Model,SerializerMixin):
    __tablename__ = "buses"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    cost_per_seat = db.Column(db.Integer, nullable=False)
    number_of_seats = db.Column(db.Integer, nullable=False)
    route = db.Column(db.String, nullable=False)
    travel_time = db.Column(db.DateTime, nullable=False)

    driver = relationship("Driver", back_populates="buses")
    schedules = relationship("Schedule", back_populates="bus")
    bookings = relationship("Booking", back_populates="bus")


class Schedule(db.Model,SerializerMixin):
    __tablename__ = "schedules"
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey("buses.id"), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    travel_date = db.Column(db.DateTime, nullable=False)

    bus= relationship("Bus", back_populates="schedules")


class Booking(db.Model,SerializerMixin):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey("buses.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    number_of_seats = db.Column(db.Integer, nullable=False)

    customer = relationship("Customer", back_populates="bookings")
    bus = relationship("Bus", back_populates="bookings")


class Driver(db.Model,SerializerMixin):
    __tablename__ = "drivers"
    id = db.Column(db.Integer, primary_key=True)
    Firstname = db.Column(db.String, nullable=False)
    Lastname = db.Column(db.String, nullable=False)
    license_number = db.Column(db.Integer, nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

    buses = relationship("Bus", back_populates="driver")


class Admin(db.Model,SerializerMixin):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
