"""
Database schema
================

sensors
    One row per physical sensor device (identified by its serial number).
    Small, rarely-changing metadata table.

measurements
    One row per persisted reading. `bucket_ts` is the *server-assigned*
    15-minute bucket the reading belongs to (see app/collector.py for how
    buckets are computed) and is UNIQUE, which is what prevents duplicate
    measurements for the same bucket even under retries/races. `measured_at`
    is the actual wall-clock time the reading was taken, kept separately so
    we never lose that information even though queries key off `bucket_ts`.

Indexes
    - measurements.bucket_ts has a UNIQUE B-tree index (also serves all
      timestamp range queries: `WHERE bucket_ts BETWEEN :from AND :to`).
    - measurements.sensor_id is indexed to support per-device lookups even
      though this app only expects a single active device.
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(primary_key=True)
    serial_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    firmware: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    measurements: Mapped[list["Measurement"]] = relationship(back_populates="sensor")


class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (
        UniqueConstraint("bucket_ts", name="uq_measurements_bucket_ts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Server-assigned 15-minute bucket. Unique -> natural duplicate guard.
    bucket_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # Actual time the collector received the reading (for debugging/audit).
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    sensor_id: Mapped[int | None] = mapped_column(
        ForeignKey("sensors.id", ondelete="SET NULL"), index=True, nullable=True
    )
    sensor: Mapped["Sensor | None"] = relationship(back_populates="measurements")

    pm01: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm02: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm003_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pm02_compensated: Mapped[float | None] = mapped_column(Float, nullable=True)

    atmp: Mapped[float | None] = mapped_column(Float, nullable=True)
    atmp_compensated: Mapped[float | None] = mapped_column(Float, nullable=True)
    rhum: Mapped[float | None] = mapped_column(Float, nullable=True)
    rhum_compensated: Mapped[float | None] = mapped_column(Float, nullable=True)

    rco2: Mapped[float | None] = mapped_column(Float, nullable=True)
    wifi: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full raw JSON payload, kept for debugging (see README for rationale).
    # Nullable / droppable via STORE_RAW_PAYLOAD=false.
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
