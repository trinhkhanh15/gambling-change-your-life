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
    target_thesis_id: str | None = Field(
        default=None, description="Id of a candidate thesis; required for UPDATE_THESIS, otherwise null"
    )
    reasoning: str = Field(
        min_length=1, description="2-3 sentence financial justification, highlighting surprise vs expectation"
    )


class ThesisUpdateDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    new_status: ThesisStatus = Field(description="KILLED if a core assumption is broken, otherwise ACTIVE")
    new_strength: float = Field(ge=0.0, le=1.0, description="Recalibrated strength; 0.0 when KILLED")
    new_evidence_points: list[str] = Field(default_factory=list, description="New supporting facts from the event")
    new_counter_evidence_points: list[str] = Field(
        default_factory=list, description="New counter-facts or risks from the event"
    )
    updated_reasoning: str = Field(min_length=1, description="How the event shifts the thesis and why")
    kill_reason: str | None = Field(default=None, description="Detailed reason if KILLED, otherwise null")
