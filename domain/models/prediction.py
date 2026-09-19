from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PredictionDirection(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"


class PredictionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RESOLVED = "RESOLVED"


class Prediction(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Unique identifier for this prediction record.")
    thesis_id: str = Field(..., description="Identifier of the thesis that produced this prediction.")
    version: int = Field(1, description="Snapshot version for this thesis prediction.")

    target: str = Field(
        ...,
        min_length=1,
        description="The asset, entity, or outcome that the prediction refers to.",
    )
    metrics: list[str] = Field(default_factory=list, description="Metrics used to evaluate the prediction.")

    direction: PredictionDirection = Field(..., description="Expected direction of the predicted outcome.")
    horizon_start: date = Field(..., description="Start date of the prediction horizon.")
    horizon_end: date = Field(..., description="End date of the prediction horizon.")
    baseline: float | None = Field(default=None, description="Reference value used for comparison, if applicable.")
    reasoning: str = Field(..., min_length=1, description="Reasoning supporting the prediction.")
    predicted_drivers: list[str] = Field(
        default_factory=list,
        description="Factors expected to influence the predicted outcome.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence in the prediction, from 0 to 1.",
    )
    resolution_criteria: list[str] = Field(
        default_factory=list,
        description="Conditions used to determine whether the prediction is resolved.",
    )
    status: PredictionStatus = Field(
        default=PredictionStatus.ACTIVE,
        description="Lifecycle status of this prediction snapshot.",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Time when this prediction snapshot was created.",
    )
    information_cutoff: datetime = Field(
        ..., description="Latest information timestamp used to create the prediction."
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, values):
        if isinstance(values, dict):
            if "predicted_divers" in values and "predicted_drivers" not in values:
                values["predicted_drivers"] = values.pop("predicted_divers")
        return values

    @field_validator("direction", mode="before")
    @classmethod
    def validate_direction(cls, value):
        if isinstance(value, PredictionDirection):
            return value
        if isinstance(value, str):
            value = value.strip().upper()
            if value in {item.value for item in PredictionDirection}:
                return PredictionDirection(value)
        raise ValueError("direction must be one of: UP, DOWN, FLAT")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        if isinstance(value, PredictionStatus):
            return value
        if isinstance(value, str):
            value = value.strip().upper()
            if value in {item.value for item in PredictionStatus}:
                return PredictionStatus(value)
        raise ValueError("status must be one of: ACTIVE, SUPERSEDED, RESOLVED")


class PredictionLLMOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    target: str = Field(..., min_length=1)
    metrics: list[str] = Field(default_factory=list)
    direction: PredictionDirection
    horizon_start: date
    horizon_end: date
    baseline: float | None = None
    reasoning: str = Field(..., min_length=1)
    predicted_drivers: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    resolution_criteria: list[str] = Field(default_factory=list)

    @field_validator("direction", mode="before")
    @classmethod
    def validate_direction(cls, value):
        if isinstance(value, PredictionDirection):
            return value
        if isinstance(value, str):
            value = value.strip().upper()
            if value in {item.value for item in PredictionDirection}:
                return PredictionDirection(value)
        raise ValueError("direction must be one of: UP, DOWN, FLAT")

