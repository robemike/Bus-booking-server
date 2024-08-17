"""Added an Image column

Revision ID: f2fe567b29cc
Revises: c1f97279e31b
Create Date: 2024-08-12 14:37:12.641064

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2fe567b29cc'
down_revision = 'c1f97279e31b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('buses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('buses', schema=None) as batch_op:
        batch_op.drop_column('image')

    # ### end Alembic commands ###