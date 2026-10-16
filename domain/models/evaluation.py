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


class EvaluationDraft(BaseModel):
    """LLM rubric output: each score is 1.0, 0.5 or 0.0 (see domain/prompts/evaluate.txt)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    direction_score: float = Field(ge=0.0, le=1.0, description="match=1.0, partial_match=0.5, no_match=0.0")
    magnitude_score: float = Field(ge=0.0, le=1.0, description="close=1.0, off=0.5, very_off=0.0")
    reason_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="support=1.0, partially_support=0.5, contradict=0.0; null if reality has no drivers to compare",
    )
    explanation: str = Field(min_length=1, description="Concise explanation of the three judgements")
