from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Feedback(BaseModel):
    """Represents feedback provided by the data."""

    agent_prediction: str
    actual_happened: str
    matching_score: float
    reasoning: str
    confidence: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Reality(BaseModel):
    """Represents the actual outcome of a prediction."""

    model_config = ConfigDict(str_strip_whitespace=True)

    target: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    actual_value: float | None = None
    actual_direction: str = Field(..., min_length=1)
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., min_length=1)
    reasoning: str = Field(..., min_length=1)
    evidence: list[str] = Field(default_factory=list)
    actual_drivers: list[str] | None = None

    @field_validator("actual_direction", mode="before")
    @classmethod
    def normalize_direction(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip().upper()
        if value in {"UP", "DOWN", "FLAT"}:
            return value
        raise ValueError("actual_direction must be one of: UP, DOWN, FLAT")


class Evaluation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    prediction_id: str = Field(..., min_length=1)
    prediction_version: int | None = None
    actual_value: float | None = None
    actual_direction: str = Field(..., min_length=1)
    direction_score: float = Field(..., ge=0.0, le=1.0)
    magnitude_score: float = Field(..., ge=0.0, le=1.0)
    reason_score: float | None = Field(default=None, ge=0.0, le=1.0)
    matching_score: float = Field(..., ge=0.0, le=100.0)
    reasoning: str = Field(..., min_length=1)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    actual_drivers: list[str] | None = None
    evaluation_status: str = "RESOLVED"

    @field_validator("actual_direction", mode="before")
    @classmethod
    def normalize_direction(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip().upper()
        if value in {"UP", "DOWN", "FLAT"}:
            return value
        raise ValueError("actual_direction must be one of: UP, DOWN, FLAT")


