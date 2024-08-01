"""initial migration

Revision ID: 7b1079f23937
Revises: 
Create Date: 2024-08-01 08:05:20.478574

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b1079f23937'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('firstname', sa.String(), nullable=False),
    sa.Column('lastname', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('phone_number', sa.Integer(), nullable=False),
    sa.Column('ID_or_Passport', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ID_or_Passport'),
    sa.UniqueConstraint('email')
    )
    op.create_table('drivers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('Firstname', sa.String(), nullable=False),
    sa.Column('Lastname', sa.String(), nullable=False),
    sa.Column('license_number', sa.Integer(), nullable=False),
    sa.Column('experience_years', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('buses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number_plate', sa.String(), nullable=False),
    sa.Column('driver_id', sa.Integer(), nullable=False),
    sa.Column('cost_per_seat', sa.Integer(), nullable=False),
    sa.Column('number_of_seats', sa.Integer(), nullable=False),
    sa.Column('route', sa.String(), nullable=False),
    sa.Column('travel_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bookings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('bus_id', sa.Integer(), nullable=False),
    sa.Column('booking_date', sa.DateTime(), nullable=True),
    sa.Column('number_of_seats', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['bus_id'], ['buses.id'], ),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('schedules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bus_id', sa.Integer(), nullable=False),
    sa.Column('departure_time', sa.DateTime(), nullable=False),
    sa.Column('arrival_time', sa.DateTime(), nullable=False),
    sa.Column('travel_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['bus_id'], ['buses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('schedules')
    op.drop_table('bookings')
    op.drop_table('buses')
    op.drop_table('drivers')
    op.drop_table('customers')
    op.drop_table('admin')
    # ### end Alembic commands ###