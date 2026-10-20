from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if "scoring_settings" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "scoring_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("engagement", sa.Float(), nullable=False),
        sa.Column("growth", sa.Float(), nullable=False),
        sa.Column("reach", sa.Float(), nullable=False),
        sa.Column("consistency", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("scoring_settings")
