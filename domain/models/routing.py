from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from domain.models.thesis import ThesisStatus


class RouterAction(str, Enum):
    GENERATE_THESIS = "GENERATE_THESIS"
    UPDATE_THESIS = "UPDATE_THESIS"
    IGNORE = "IGNORE"


class RouterDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: RouterAction
    target_thesis_id: str | None = None
    reasoning: str = Field(min_length=1)


class ThesisUpdateDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    new_status: ThesisStatus
    new_strength: float = Field(ge=0.0, le=1.0)
    new_evidence_points: list[str] = Field(default_factory=list)
    new_counter_evidence_points: list[str] = Field(default_factory=list)
    updated_reasoning: str = Field(min_length=1)
    kill_reason: str | None = None
