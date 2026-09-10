from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EventNature(str, Enum):
    FACT = "fact"
    EXPECTATION = "expectation"


class EventScope(str, Enum):
    COMPANY = "company"
    INDUSTRY = "industry"
    MACRO = "macro"


class ThesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    KILLED = "KILLED"


class RouterAction(str, Enum):
    GENERATE_THESIS = "GENERATE_THESIS"
    UPDATE_THESIS = "UPDATE_THESIS"
    IGNORE = "IGNORE"


class ExpectationContext(BaseModel):
    consensus_metric: Optional[str] = Field(None, description="Tên chỉ số (EPS, Revenue, Shipments...)")
    expected_value: Optional[str] = Field(None, description="Giá trị thị trường đã kỳ vọng trước đó")
    actual_value: Optional[str] = Field(None, description="Giá trị thực tế vừa công bố")
    surprise_direction: Optional[str] = Field(None, description="'BEAT', 'MISS', hoặc 'IN_LINE'")


class Event(BaseModel):
    id: str = Field(..., description="Mã định danh duy nhất của event")
    published_at: datetime = Field(..., description="Thời gian phát hành tin tức")
    source: str = Field(..., description="Nguồn tin tức (Reuters, Bloomberg, 8-K...)")
    title: str = Field(..., description="Tiêu đề sự kiện")
    content: str = Field(..., description="Nội dung chi tiết của sự kiện")
    companies_mentioned: List[str] = Field(default_factory=list, description="Mã ticker các công ty liên quan chính")
    sectors: List[str] = Field(default_factory=list, description="Nhóm ngành nghề")
    nature: EventNature = Field(..., description="Bản chất tin tức: fact hay expectation")
    scope: EventScope = Field(..., description="Phạm vi tác động: company, industry, macro")
    expectation_context: Optional[ExpectationContext] = Field(None, description="Bối cảnh kỳ vọng để phát hiện surprise")


class EvidenceItem(BaseModel):
    event_id: str = Field(..., description="ID của event cung cấp bằng chứng")
    timestamp: datetime = Field(..., description="Thời điểm ghi nhận bằng chứng")
    point: str = Field(..., description="Nội dung luận chứng trích xuất từ event")


class Thesis(BaseModel):
    id: str = Field(..., description="Mã định danh thesis (ví dụ: THESIS-NVDA-001)")
    ticker: str = Field(..., description="Mã ticker chính")
    core_claim: str = Field(..., description="Luận điểm cốt lõi (BẤT BIẾN một khi đã tạo)")
    core_assumptions: List[str] = Field(
        ..., 
        description="Các giả định then chốt làm cơ sở cho thesis. Nếu bị đập gãy -> KILL thesis"
    )
    status: ThesisStatus = Field(default=ThesisStatus.ACTIVE, description="Trạng thái ACTIVE hoặc KILLED")
    strength: float = Field(
        ..., ge=0.0, le=1.0, 
        description="Mức độ bằng chứng hỗ trợ thesis hiện tại (0.0 đến 1.0)"
    )
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Danh sách bằng chứng ủng hộ")
    counter_evidence: List[EvidenceItem] = Field(default_factory=list, description="Danh sách bằng chứng phản bác/rủi ro")
    reasoning: str = Field(..., description="Lập luận tổng hợp trạng thái hiện tại")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm tạo (Time-lock)")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm cập nhật mới nhất")
    killed_at: Optional[datetime] = Field(None, description="Thời điểm bị hủy bỏ (nếu có)")
    kill_reason: Optional[str] = Field(None, description="Lý do chi tiết khi thesis bị KILL")


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
