from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.models.event import Evidence


class ThesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    KILLED = "KILLED"


class Thesis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    core_claim: str = Field(min_length=1)
    core_assumptions: list[str] = Field(min_length=1)
    status: ThesisStatus = ThesisStatus.ACTIVE
    strength: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    counter_evidence: list[Evidence] = Field(default_factory=list)
    reasoning: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    killed_at: datetime | None = None
    kill_reason: str | None = None

    @model_validator(mode="after")
    def validate_killed_state(self):
        if self.status == ThesisStatus.KILLED:
            if self.strength != 0.0 or not self.kill_reason:
                raise ValueError("a killed thesis must have zero strength and a kill reason")
        return self


class ThesisDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1)
    core_claim: str = Field(min_length=1)
    core_assumptions: list[str] = Field(min_length=1)
    initial_strength: float = Field(ge=0.0, le=1.0)
    evidence_points: list[str] = Field(min_length=1)
    counter_evidence_points: list[str] = Field(min_length=1)
    reasoning: str = Field(min_length=1)
