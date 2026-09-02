from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SensorReadingRaw(BaseModel):
    """Shape of the JSON returned by the physical sensor's HTTP API.

    Extra fields (boot, bootCount, serialno, firmware, model, ...) are
    allowed and ignored/used selectively - the sensor firmware may add
    fields over time and we don't want that to break collection.
    """

    model_config = ConfigDict(extra="ignore")

    pm01: float | None = None
    pm02: float | None = None
    pm10: float | None = None
    pm003Count: float | None = None
    pm02Compensated: float | None = None
    atmp: float | None = None
    atmpCompensated: float | None = None
    rhum: float | None = None
    rhumCompensated: float | None = None
    rco2: float | None = None
    wifi: int | None = None
    serialno: str | None = None
    firmware: str | None = None
    model: str | None = None


class MeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bucket_ts: datetime
    measured_at: datetime
    pm01: float | None
    pm02: float | None
    pm10: float | None
    pm003_count: float | None
    pm02_compensated: float | None
    atmp: float | None
    atmp_compensated: float | None
    rhum: float | None
    rhum_compensated: float | None
    rco2: float | None
    wifi: int | None


class AggregatedPoint(BaseModel):
    """One aggregated bucket, used when a query range is downsampled."""

    bucket_ts: datetime
    pm01_avg: float | None = None
    pm02_avg: float | None = None
    pm02_min: float | None = None
    pm02_max: float | None = None
    pm10_avg: float | None = None
    rco2_avg: float | None = None
    rco2_min: float | None = None
    rco2_max: float | None = None
    atmp_avg: float | None = None
    rhum_avg: float | None = None
    sample_count: int


class Resolution(str, Enum):
    raw = "raw"
    aggregated = "aggregated"


class MeasuresResponse(BaseModel):
    resolution: Resolution
    from_ts: datetime
    to_ts: datetime
    raw: list[MeasurementOut] = Field(default_factory=list)
    aggregated: list[AggregatedPoint] = Field(default_factory=list)


class HealthStatus(BaseModel):
    status: str
    database: str
    sensor: str
    last_measurement_at: datetime | None = None
    timezone: str
