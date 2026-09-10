# Đặc Tả Kỹ Thuật: Analysis Layer & Schemas (Week 1 Focus)
> Cập nhật theo kết luận mới nhất về phân tách Thesis vs Prediction và chuẩn hóa trường `strength`.

---

## 1. Tổng Hợp & Thống Nhất Thiết Kế Kiến Trúc

| Vấn đề | Thiết kế cũ (Sơ khai) | **Cập Nhật Thống Nhất Mới Nhất** |
| :--- | :--- | :--- |
| **Thước đo Thesis** | Dùng `confidence` và kill khi confidence < threshold | **Chuyển thành `strength` (0.0 đến 1.0)**.<br>• `confidence`: Dành riêng cho Prediction (độ tự tin của model dự báo, dùng cho calibration trong feedback loop).<br>• `strength`: Dành riêng cho Thesis, thể hiện mức độ bằng chứng hiện tại đang ủng hộ hay phản bác luận điểm. |
| **Cơ chế Kill Thesis** | Kill tự động theo threshold số học | **LLM quyết định Kill dựa trên Bằng chứng & Giả định cốt lõi (`core_assumptions`)**.<br>Ở MVP, với mỗi thesis gồm evidence/counter-evidence, LLM đánh giá xem giả định cốt lõi có bị đập gãy hay không để quyết định Kill (kèm `kill_reason` tường minh). |
| **Phân tách Thesis vs Prediction** | Dễ bị nhầm lẫn giữa cập nhật luận điểm và đánh giá dự báo | **Tách bạch dứt khoát**:<br>• **Thesis**: Có thể được `generate` / `update` / `kill` bằng cách phân tích Event.<br>• **Prediction**: Là output phái sinh từ Thesis, có target/horizon cụ thể ($T+1, T+30$). Có thể được `generate` / `update` (supersede và lưu version cũ), nhưng **CHỈ có thể bị kill/evaluate bởi Reality** (khi có dữ liệu thực tế tại ngày đáo hạn). |
| **Phân tầng Layer** | Gộp Improve Layer vào Event Layer hôm sau | **Tách riêng Resolution & Evaluation Layer**:<br>• *Event Layer*: Chỉ thu thập & tiền xử lý tin tức phục vụ phân tích Thesis.<br>• *Resolution & Evaluation Layer*: Chịu trách nhiệm lấy dữ liệu thực tế (Reality) để đối chiếu và tính Matching Score với Prediction. |

---

## 2. Chuẩn Hóa Data Schemas

### 2.1. Event Schema (Hỗ trợ Fundamental & Expectation)

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class EventNature(str, Enum):
    FACT = "fact"                # Dữ liệu thực tế: Earnings report, SEC filing, số liệu thống kê
    EXPECTATION = "expectation"  # Kỳ vọng/Dự báo: Management guidance, analyst consensus, tin đồn

class EventScope(str, Enum):
    COMPANY = "company"
    INDUSTRY = "industry"
    MACRO = "macro"

class ExpectationContext(BaseModel):
    consensus_metric: Optional[str] = Field(None, description="Chỉ số kỳ vọng (EPS, Revenue...)")
    expected_value: Optional[str] = Field(None, description="Kỳ vọng trước tin")
    actual_value: Optional[str] = Field(None, description="Thực tế công bố")
    surprise_direction: Optional[str] = Field(None, description="'BEAT', 'MISS', hoặc 'IN_LINE'")

class Event(BaseModel):
    id: str
    published_at: datetime
    source: str
    title: str
    content: str
    companies_mentioned: List[str] = []
    sectors: List[str] = []
    nature: EventNature
    scope: EventScope
    expectation_context: Optional[ExpectationContext] = None
```

### 2.2. Thesis Schema (Core Claim Bất Biến, Dynamic Strength & Evidence)

```python
class ThesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    KILLED = "KILLED"

class EvidenceItem(BaseModel):
    event_id: str
    timestamp: datetime
    point: str

class Thesis(BaseModel):
    id: str
    ticker: str
    core_claim: str
    core_assumptions: List[str]
    status: ThesisStatus = ThesisStatus.ACTIVE
    strength: float = Field(..., ge=0.0, le=1.0, description="Độ vững chắc hỗ trợ bởi evidence hiện tại")
    evidence: List[EvidenceItem] = []
    counter_evidence: List[EvidenceItem] = []
    reasoning: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    killed_at: Optional[datetime] = None
    kill_reason: Optional[str] = None
```

### 2.3. Router Decision Schema

```python
class RouterAction(str, Enum):
    GENERATE_THESIS = "GENERATE_THESIS"
    UPDATE_THESIS = "UPDATE_THESIS"
    IGNORE = "IGNORE"

class RouterDecision(BaseModel):
    action: RouterAction
    target_thesis_id: Optional[str] = None
    reasoning: str
```

---

## 3. Vòng Đời Kiểm Thử 5 Event Mẫu (DoD)

Hệ thống đã kiểm chứng thành công trên cổ phiếu **NVDA**:
1. **Event 1 (GENERATE_THESIS)**: Q1 FY2026 Earnings beat + Guidance raise $\rightarrow$ Sinh Thesis mới (`strength: 0.75`).
2. **Event 2 (UPDATE_THESIS)**: MSFT & GOOGL mở rộng CapEx AI 30% $\rightarrow$ Thêm evidence, củng cố thesis (`strength: 0.85`).
3. **Event 3 (UPDATE_THESIS)**: TSMC nghẽn đóng gói CoWoS $\rightarrow$ Thêm counter-evidence, hạ `strength: 0.70`, giữ `ACTIVE`.
4. **Event 4 (UPDATE_THESIS $\rightarrow$ KILL)**: Big Tech đóng băng đơn GPU, chuyển sang chip ASIC tự phát triển $\rightarrow$ Phá vỡ Core Assumptions 1 & 3 $\rightarrow$ `status: KILLED`, `strength: 0.0` kèm `kill_reason` tường minh.
5. **Event 5 (IGNORE)**: CEO Jensen Huang làm từ thiện & phát biểu Stanford $\rightarrow$ Bỏ qua do không ảnh hưởng đến dòng tiền kinh doanh.
