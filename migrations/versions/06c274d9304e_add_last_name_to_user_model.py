"""Add last_name to User model

Revision ID: 06c274d9304e
Revises: 39e5aa954181
Create Date: 2024-10-16 23:10:53.406787

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '06c274d9304e'
down_revision = '39e5aa954181'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_name', sa.String(length=100), nullable=False))
        batch_op.drop_column('surname')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('surname', mysql.VARCHAR(length=100), nullable=False))
        batch_op.drop_column('last_name')

    # ### end Alembic commands ###
