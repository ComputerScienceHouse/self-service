"""empty message

Revision ID: a541afdca952
Revises: a83f363599a0
Create Date: 2018-09-18 19:03:05.250697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a541afdca952'
down_revision = 'a83f363599a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('app_passwds',
    sa.Column('user', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('user')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('app_passwds')
    # ### end Alembic commands ###
