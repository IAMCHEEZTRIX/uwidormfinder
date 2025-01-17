"""Rename column and add new column to rooms table

Revision ID: 917fb0e287b5
Revises: bfecf618b791
Create Date: 2024-11-25 08:04:59.229634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '917fb0e287b5'
down_revision = 'bfecf618b791'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rooms', schema=None) as batch_op:
        batch_op.add_column(sa.Column('building', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('floor_number', sa.Integer(), nullable=False))
        batch_op.drop_column('room_floor')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rooms', schema=None) as batch_op:
        batch_op.add_column(sa.Column('room_floor', sa.INTEGER(), nullable=False))
        batch_op.drop_column('floor_number')
        batch_op.drop_column('building')

    # ### end Alembic commands ###
