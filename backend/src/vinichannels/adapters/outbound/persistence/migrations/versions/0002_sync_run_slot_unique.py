from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("sync_runs", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_sync_runs_slot", ["channel_id", "scheduled_for", "trigger"]
        )


def downgrade() -> None:
    with op.batch_alter_table("sync_runs", schema=None) as batch_op:
        batch_op.drop_constraint("uq_sync_runs_slot", type_="unique")
