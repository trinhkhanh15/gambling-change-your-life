from datetime import date, datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"


class PredictionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RESOLVED = "RESOLVED"
    INVALIDATED = "INVALIDATED"


class Prediction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    thesis_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    target: str = Field(min_length=1)
    metrics: list[str] = Field(min_length=1)
    direction: Direction
    horizon_start: date
    horizon_end: date
    baseline: float
    expected_change_pct: float
    predicted_drivers: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    resolution_criteria: list[str] = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    status: PredictionStatus = PredictionStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    information_cutoff: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_horizon_and_direction(self):
        if self.horizon_end < self.horizon_start:
            raise ValueError("horizon_end must be on or after horizon_start")
        if self.direction == Direction.UP and self.expected_change_pct <= 0:
            raise ValueError("UP predictions must have a positive expected change")
        if self.direction == Direction.DOWN and self.expected_change_pct >= 0:
            raise ValueError("DOWN predictions must have a negative expected change")
        if self.direction == Direction.FLAT and self.expected_change_pct != 0:
            raise ValueError("FLAT predictions must have zero expected change")
        return self


class PredictionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    target: str = Field(min_length=1, description="Observable target, e.g. the stock ticker")
    metrics: list[str] = Field(min_length=1, description="Observable metrics, e.g. price_return")
    direction: Direction
    horizon_start: date
    horizon_end: date
    baseline: float = Field(description="Reference value at horizon_start")
    expected_change_pct: float = Field(
        description="Decimal fraction (0.03 = +3%, -0.05 = -5%); positive for UP, negative for DOWN, 0 for FLAT"
    )
    predicted_drivers: list[str] = Field(min_length=1, description="Main causal drivers behind the prediction")
    confidence: float = Field(ge=0.0, le=1.0)
    resolution_criteria: list[str] = Field(min_length=1, description="Objective, observable resolution rules")
    reasoning: str = Field(min_length=1, description="Causal reasoning; what is new relative to market expectations")


class PredictionChange(str, Enum):
    NO_CHANGE = "no_change"
    MINOR_CHANGE = "minor_change"
    MAJOR_CHANGE = "major_change"


class PredictionComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    change: PredictionChange = Field(description="Only major_change creates a new prediction version")
    changed_fields: list[str] = Field(default_factory=list, description="Fields that materially changed")
    explanation: str = Field(min_length=1, description="Why the change is or is not material")
