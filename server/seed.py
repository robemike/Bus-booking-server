from datetime import datetime
from app import db  # Replace with your actual app import
from models import Customer, Bus, Schedule, Booking, Driver, Admin  # Adjust as necessary
from faker import Faker
import re

fake = Faker()

def clear_db():
    """Clears the entire database."""
    with app.app_context():
        db.drop_all()
        db.create_all()

def generate_number_plate():
    """Generates a random number plate in the format ABC123."""
    letters = ''.join(fake.random_choices(elements='ABCDEFGHIJKLMNOPQRSTUVWXYZ', length=3))
    numbers = ''.join(fake.random_choices(elements='0123456789', length=3))
    number_plate = f"{letters}{numbers}"
    print(f"Generated number plate: {number_plate}")  # Debug print
    return number_plate

def validate_number_plate(value):
    """Validates the number plate format."""
    if not re.match(r'^[A-Z]{3}[0-9]{3}$', value):
        print(f"Invalid number plate: {value}")  
        raise ValueError("Invalid number plate format")
    return value


def seed_data():
    clear_db() 
    
    # Create example customers
    customers = []
    for _ in range(5):
        phone_number = str(fake.random_int(min=6000000000, max=9999999999))
        customer = Customer(
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            email=fake.unique.email(),
            password=fake.password(),
            address=fake.address(),
            phone_number=phone_number,
            id_or_passport=str(fake.unique.random_int(min=100000000, max=999999999))
        )
        customers.append(customer)

    db.session.add_all(customers)
    db.session.commit()

    # Create example drivers
    drivers = []
    for _ in range(2):
        driver = Driver(
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            license_number=str(fake.unique.random_int(min=100000000, max=999999999)),
            experience_years=fake.random_int(min=1, max=10),
            phone_number=str(fake.random_int(min=6000000000, max=9999999999)),
            email=fake.unique.email(),
            password=fake.password()
        )
        drivers.append(driver)

    db.session.add_all(drivers)
    db.session.commit()


    buses = []
    for i in range(2):  
        number_plate = generate_number_plate()
        validated_number_plate = validate_number_plate(number_plate)  # Validate the number plate

        bus = Bus(
            username=fake.company(),
            driver_id=drivers[i].id,
            cost_per_seat=fake.random_int(min=100, max=200),
            number_of_seats=fake.random_int(min=30, max=50),
            route=fake.street_name(),
            travel_time=datetime(2024, 8, 10, 14, 0),
            number_plate=validated_number_plate 
                            )
        buses.append(bus)

    db.session.add_all(buses)
    db.session.commit()

    # Create example schedules
    schedules = []
    for bus in buses:
        schedule = Schedule(
            bus_id=bus.id,
            departure_time=datetime(2024, 8, 10, 14, 30),
            arrival_time=datetime(2024, 8, 10, 16, 30),
            travel_date=datetime(2024, 8, 10),
            available_seats=bus.number_of_seats,
            occupied_seats=0
        )
        schedules.append(schedule)

    db.session.add_all(schedules)
    db.session.commit()

    # Create example bookings
    bookings = []
    for i, customer in enumerate(customers):
        booking = Booking(
            customer_id=customer.id,
            bus_id=buses[i % len(buses)].id,
            number_of_seats=fake.random_int(min=1, max=5),
            booking_date=datetime.utcnow()
        )
        bookings.append(booking)

    db.session.add_all(bookings)
    db.session.commit()

    # Create example admin
    admin = Admin(
        username="admin_user",
        email="admin@example.com",
        password="hashed_admin_password"
    )

    db.session.add(admin)
    db.session.commit()

if __name__ == "__main__":
    from app import app  
    
    with app.app_context():
        seed_data()
