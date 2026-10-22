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

    ticker: str = Field(min_length=1, description="Primary stock ticker the thesis is about, or 'NONE' if not company-specific")
    core_claim: str = Field(min_length=1, description="Concise fundamental claim (BULLISH or BEARISH); immutable once created")
    core_assumptions: list[str] = Field(
        min_length=1, description="2-3 falsifiable conditions; if one breaks, the thesis is killed"
    )
    initial_strength: float = Field(
        ge=0.0, le=1.0, description="How strongly the current evidence supports the thesis (0.20-0.85). Low values (0.20-0.45) for negative/vulnerable developments, high values (0.65-0.85) for confirmed catalysts"
    )
    evidence_points: list[str] = Field(min_length=1, description="Facts from the event that support the thesis")
    counter_evidence_points: list[str] = Field(
        min_length=1, description="Risks or counter-arguments; at least one is required"
    )
    reasoning: str = Field(min_length=1, description="Why the event's surprise matters for long-term business drivers")
