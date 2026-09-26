from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.models.prediction import Direction


class Reality(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    prediction_id: str = Field(min_length=1)
    target: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    baseline: float
    actual_value: float
    actual_direction: Direction
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    actual_drivers: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_direction(self):
        if self.baseline == 0:
            raise ValueError("baseline cannot be zero when deriving percentage change")
        derived = self.actual_change_pct
        expected = Direction.UP if derived > 0 else Direction.DOWN if derived < 0 else Direction.FLAT
        if self.actual_direction != expected:
            raise ValueError("actual_direction must match the observed values and baseline")
        return self

    @property
    def actual_change_pct(self) -> float:
        return (self.actual_value - self.baseline) / abs(self.baseline)
