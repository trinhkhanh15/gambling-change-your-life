from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from domain.schema.thesis import ThesisStatus


class RouterAction(str, Enum):
    GENERATE_THESIS = "GENERATE_THESIS"
    UPDATE_THESIS = "UPDATE_THESIS"
    IGNORE = "IGNORE"


class RouterDecision(BaseModel):
    action: RouterAction = Field(..., description="Hành động định tuyến: GENERATE_THESIS, UPDATE_THESIS, hoặc IGNORE")
    target_thesis_id: Optional[str] = Field(None, description="Mã thesis mục tiêu khi action == UPDATE_THESIS")
    reasoning: str = Field(..., description="Lập luận giải thích lý do định tuyến")


class ThesisGenerateOutput(BaseModel):
    ticker: str
    core_claim: str
    core_assumptions: List[str]
    initial_strength: float = Field(..., ge=0.0, le=1.0)
    evidence_points: List[str] = Field(default_factory=list)
    counter_evidence_points: List[str] = Field(default_factory=list)
    reasoning: str


class ThesisUpdateOutput(BaseModel):
    new_status: ThesisStatus
    kill_reason: Optional[str] = None
    new_strength: float = Field(..., ge=0.0, le=1.0)
    new_evidence_points: List[str] = Field(default_factory=list)
    new_counter_evidence_points: List[str] = Field(default_factory=list)
    updated_reasoning: str
