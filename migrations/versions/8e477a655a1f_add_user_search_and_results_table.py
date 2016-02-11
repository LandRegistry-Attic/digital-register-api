"""Add 'User Search And Results' table

Revision ID: 8e477a655a1f
Revises: 18124bf31811
Create Date: 2016-02-11 16:17:17.691417

"""

# revision identifiers, used by Alembic.
revision = '8e477a655a1f'
down_revision = '18124bf31811'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_search_and_results',
    sa.Column('viewed_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('user_id', sa.String(length=20), nullable=False),
    sa.Column('title_number', sa.String(length=20), nullable=False),
    sa.Column('search_type', sa.String(length=20), nullable=False),
    sa.Column('purchase_type', sa.String(length=1), nullable=False),
    sa.Column('amount', sa.String(length=10), nullable=False),
    sa.Column('cart_id', sa.String(length=30), nullable=True),
    sa.Column('transaction_id', sa.String(length=30), nullable=True),
    sa.PrimaryKeyConstraint('viewed_time', 'user_id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_search_and_results')
    ### end Alembic commands ###
