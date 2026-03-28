"""save phone number

Revision ID: ada3c91a553e
Revises: fdb69cd98e19
Create Date: 2026-02-18 21:07:12.041639

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ada3c91a553e"
down_revision = "fdb69cd98e19"
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
