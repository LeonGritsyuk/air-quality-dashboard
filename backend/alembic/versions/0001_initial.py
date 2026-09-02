"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("serial_no", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("firmware", sa.String(length=64), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sensors_serial_no", "sensors", ["serial_no"], unique=True)

    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bucket_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "sensor_id",
            sa.Integer(),
            sa.ForeignKey("sensors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("pm01", sa.Float(), nullable=True),
        sa.Column("pm02", sa.Float(), nullable=True),
        sa.Column("pm10", sa.Float(), nullable=True),
        sa.Column("pm003_count", sa.Integer(), nullable=True),
        sa.Column("pm02_compensated", sa.Float(), nullable=True),
        sa.Column("atmp", sa.Float(), nullable=True),
        sa.Column("atmp_compensated", sa.Float(), nullable=True),
        sa.Column("rhum", sa.Float(), nullable=True),
        sa.Column("rhum_compensated", sa.Float(), nullable=True),
        sa.Column("rco2", sa.Float(), nullable=True),
        sa.Column("wifi", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.UniqueConstraint("bucket_ts", name="uq_measurements_bucket_ts"),
    )
    op.create_index("ix_measurements_bucket_ts", "measurements", ["bucket_ts"])
    op.create_index("ix_measurements_sensor_id", "measurements", ["sensor_id"])


def downgrade() -> None:
    op.drop_index("ix_measurements_sensor_id", table_name="measurements")
    op.drop_index("ix_measurements_bucket_ts", table_name="measurements")
    op.drop_table("measurements")
    op.drop_index("ix_sensors_serial_no", table_name="sensors")
    op.drop_table("sensors")
