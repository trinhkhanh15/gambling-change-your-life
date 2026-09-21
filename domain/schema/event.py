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


class DecomposedEventItem(BaseModel):
    title: str = Field(...)
    content: str = Field(...)
    companies_mentioned: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)
    nature: EventNature = EventNature.FACT
    scope: EventScope = EventScope.COMPANY
    expectation_context: Optional[ExpectationContext] = None


class EventDecompositionOutput(BaseModel):
    events: List[DecomposedEventItem] = Field(default_factory=list)

