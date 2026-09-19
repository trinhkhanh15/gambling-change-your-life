from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ThesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    KILLED = "KILLED"


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
