"""save phone number

Revision ID: ada3c91a553e
Revises: 92c9d8ea5b74
Create Date: 2026-02-18 21:07:12.041639

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ada3c91a553e"
down_revision = "92c9d8ea5b74"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "phone_codes", "code", new_column_name="phone_number", type_=sa.String(12)
    )
    op.drop_constraint("phone_codes_pkey", "phone_codes", type_="primary")


def downgrade():
    op.create_primary_key("phone_codes_pkey", "phone_codes", ["code"])
    op.alter_column(
        "phone_codes", "phone_number", new_column_name="code", type_=sa.String(6)
    )
