from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class Evaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    prediction_id: str = Field(min_length=1)
    prediction_version: int = Field(ge=1)
    reality_id: str = Field(min_length=1)
    direction_score: float = Field(ge=0.0, le=1.0)
    magnitude_score: float = Field(ge=0.0, le=1.0)
    reason_score: float | None = Field(default=None, ge=0.0, le=1.0)
    matching_score: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
