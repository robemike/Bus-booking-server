from datetime import date, timedelta, time
from app import db, app  
from models import Customer, Bus, Schedule, Booking, Driver, Admin
from faker import Faker
import re

fake = Faker()

def clear_db():
    """Clears the entire database."""
    with app.app_context():
        db.drop_all()
        db.create_all()


def seed_data():
    clear_db()
    
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
            id_or_passport=str(fake.unique.random_int(min=10000000, max=99999999))  # Adjusted to 8 digits
        )
        customers.append(customer)

    try:
        db.session.add_all(customers)
        db.session.commit()
        print(f"Seeded {len(customers)} customers.")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding customers: {str(e)}")

    drivers = []
    for _ in range(2):
        driver = Driver(
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            license_number=str(fake.unique.random_int(min=10000000, max=99999999)),  # Adjusted to 8 digits
            experience_years=fake.random_int(min=1, max=10),
            phone_number=str(fake.random_int(min=6000000000, max=9999999999)),
            email=fake.unique.email(),
            password=fake.password()
        )
        drivers.append(driver)

    db.session.add_all(drivers)
    db.session.commit()
    print(f"Seeded {len(drivers)} drivers.")

    buses = []
    for i in range(2):

        bus = Bus(
            username=fake.company(),
            driver_id=drivers[i].id,
            cost_per_seat=fake.random_int(min=100, max=200),
            number_of_seats=fake.random_int(min=30, max=50),
            route=fake.street_name(),
            travel_time=time(hour=fake.random_int(min=6, max=22), minute=fake.random_int(min=0, max=59))  # Random time for travel 
        )
        buses.append(bus)

    db.session.add_all(buses)
    db.session.commit()
    print(f"Seeded {len(buses)} buses.")

    schedules = []
    for bus in buses:
        schedule = Schedule(
            bus_id=bus.id,
            departure_time=time(hour=14, minute=30),  # Time object
            arrival_time=time(hour=16, minute=30),    # Time object
            travel_date=date.today() + timedelta(days=fake.random_int(min=1, max=30)),  # Future travel date
            available_seats=bus.number_of_seats,
            occupied_seats=0
        )
        schedules.append(schedule)

    db.session.add_all(schedules)
    db.session.commit()
    print(f"Seeded {len(schedules)} schedules.")

    bookings = []
    for customer in customers:
        booking = Booking(
            customer_id=customer.id,
            bus_id=buses[fake.random_int(min=0, max=len(buses) - 1)].id,  # Random bus selection
            number_of_seats=fake.random_int(min=1, max=5),
            booking_date=date.today(),  # Set to today's date
            total_cost=0,  # Initialize to 0; will be calculated in the save method
            selected_seats=fake.random_element(elements=('1A', '1B', '1C', '2A', '2B')),  # Random seat selection
            destination=fake.city(),
            departure_time=time(hour=fake.random_int(min=6, max=22), minute=fake.random_int(min=0, max=59)),  # Random time for departure
            current_address=fake.address()
        )
        bookings.append(booking)

    # Calculate total cost for bookings
    for booking in bookings:
        booking.total_cost = booking.number_of_seats * booking.bus.cost_per_seat  # Calculate total cost

    db.session.add_all(bookings)
    db.session.commit()
    print(f"Seeded {len(bookings)} bookings.")

    admin = Admin(
        username="admin_user",
        email="admin@example.com",
        password="hashed_admin_password"
    )

    db.session.add(admin)
    db.session.commit()
    print("Seeded admin.")

if __name__ == "__main__":  
    with app.app_context():
        seed_data()
