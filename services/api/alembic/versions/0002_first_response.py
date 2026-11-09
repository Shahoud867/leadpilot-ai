"""Separate staff response SLA from customer replies."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # 0001 is the LP-1 schema snapshot in this release and already includes this
    # column for fresh databases. Existing 0001 demos receive it here.
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("leads")}
    if "first_response_at" not in cols:
        op.add_column(
            "leads", sa.Column("first_response_at", sa.String(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("leads") as batch:
        batch.drop_column("first_response_at")
