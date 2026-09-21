# Nhật Ký Triển Khai (Implementation Log) — Event & Analysis Layers Pipeline

> **Dự án**: Financial Research Agent (`gambling-change-your-life`)  
> **Nhiệm vụ tuần**: Chốt Event/Thesis Schema, Implement Router, Update Evidence/Counter-Evidence, Generate Thesis, Kill Decision.  
> **Definition of Done (DoD)**: Cho 3–5 event mẫu vào, system tạo/update/kill thesis đúng format, có reasoning.  
> **Trạng thái**: ✅ ĐÃ HOÀN THÀNH & TÁI CẤU TRÚC THEO LAYER ARCHITECTURE (Tham khảo `origin/thuan` và `origin/eric-dev`).

---

## 1. Nhật Ký Thực Hiện Từng Bước (Step-by-Step Log)

### Bước 1: Nghiên cứu tài liệu và phân tích yêu cầu
- **Nguồn tài liệu**: Đối chiếu `planning.md`, `finance_bootcamp.md`, `analysis_layer_spec.md`, cùng mã nguồn nhánh `eric-dev` và `origin/thuan`.
- **Quyết định thiết kế**:
  1. Thống nhất cơ chế **2-Stage Routing**: Stage 1 lọc Candidate Theses theo vector/keyword tương đồng (tiết kiệm token cost); Stage 2 dùng LLM quyết định `GENERATE_THESIS`, `UPDATE_THESIS`, hoặc `IGNORE`.
  2. Bổ sung trường `expectation_context` vào Event Schema để đo lường 2 chiều: **Fundamental vs Expectation** (phát hiện Beat/Miss/Surprise so với Priced-in).
  3. Cố định tính bất biến của `core_claim` trong Thesis. Mọi biến động được ghi nhận qua `evidence`, `counter_evidence`, `strength`, và `reasoning`.
  4. Quyết định Kill Thesis do LLM đánh giá dựa trên việc **giả định cốt lõi (`core_assumptions`)** có bị đập gãy hay không (không dùng threshold số học cứng).
  5. Tách biệt hoàn toàn Thesis vs Prediction: Prediction là phái sinh từ Thesis, chỉ bị evaluate bởi Reality ở ngày đáo hạn.

### Bước 2: Tái cấu trúc chuẩn hóa Schema & Prompts (Domain-Driven Design)
- **Thư mục Schema chuyên biệt (`domain/schema/`)**:
  - `event.py`: `Event`, `EventNature`, `EventScope`, `ExpectationContext`, `DecomposedEventItem`, `EventDecompositionOutput`.
  - `thesis.py`: `Thesis`, `ThesisStatus`, `EvidenceItem`.
  - `router.py`: `RouterAction`, `RouterDecision`, `ThesisGenerateOutput`, `ThesisUpdateOutput`.
- **Thư mục Prompt chuyên biệt (`domain/prompts/`)**:
  - `router.txt`: Định tuyến tin tức vào Candidate Theses.
  - `generate_thesis.txt`: Thiết lập luận điểm và giả định cốt lõi.
  - `update_kill_thesis.txt`: Cập nhật bằng chứng, tái cân bằng strength và đưa ra quyết định Kill.
  - `decompose_event.txt`: Tiêu chí phân tách bản tin phức hợp thành các sự kiện nguyên tử.
  - Render tự động thông qua `service/shared/prompt_renderer.py`.

### Bước 3: Đơn giản hóa LLM Interface (Tham khảo `origin/thuan`)
- **Loại bỏ hàm thừa ở Base LLM**: Xóa bỏ `BaseLLMClient` với các hàm nghiệp vụ riêng lẻ (`route_event`, `generate_thesis`,...).
- **Giao diện LLM duy nhất**: Cả `OpenAIClient` và `MockLLMClient` chỉ cung cấp đúng 1 phương thức:
  ```python
  generate_response(system_prompt: str, response_model: Optional[Type[BaseModel]] = None) -> Union[str, Any]
  ```
- **Vai trò của `MockLLMClient`**:
  - Giả lập phản hồi LLM cục bộ có quy luật phục vụ chạy Unit Test tự động / CI-CD siêu tốc và miễn phí (không tốn chi phí API token).
  - Đảm bảo tính tất định (deterministic) 100% khi kiểm thử State Machine.
  - Cho phép dev khác trong team code và chạy thử offline khi chưa cấu hình `OPENAI_API_KEY`.
  - Cùng interface với `OpenAIClient` giúp cắm API key vào là chạy production ngay, không cần sửa code layer.

### Bước 4: Tái cấu trúc thành các Layer độc lập (`service/pipelines/layers/`)
- Thay vì phân tán vào các agent nhỏ trong `service/agents/`, mỗi layer được đóng gói thành một class lớn:
  1. `EventLayer` (`service/pipelines/layers/event_layer.py`):
     - Intake dữ liệu tin thô hoặc dict/object.
     - Validate vào `Event` schema.
     - Hỗ trợ `decompose_news()` bóc tách bản tin đa chủ đề thành danh sách các `Event` nguyên tử dựa trên các tiêu chí: Ticker, Horizon (quá khứ vs tương lai), và Business Dimension.
  2. `AnalysisLayer` (`service/pipelines/layers/analysis_layer.py`):
     - Quản lý state danh sách `theses` (`Dict[str, Thesis]`) và `event_log`.
     - Lọc `candidate_theses` (Top-K) phù hợp nhất với event.
     - Tự render prompt và gọi trực tiếp `self.llm.generate_response()` cho từng tác vụ Routing, Thesis Generation, và Thesis Update/Kill.
     - Cung cấp các helper: `get_active_theses()`, `get_killed_theses()`, `get_thesis()`.
- Loại bỏ hoàn toàn `analysis_pipeline.py` để tránh dư thừa và chuẩn hóa việc gọi trực tiếp qua `AnalysisLayer`.

### Bước 5: Kiểm thử nghiệm thu Definition of Done (DoD)
- Cập nhật `tests/test_pipeline.py` kiểm thử luồng phối hợp giữa `EventLayer` và `AnalysisLayer`.
- Chạy lệnh: `./.venv/bin/python tests/test_pipeline.py`.
- **Kết quả**: 100% assertions passed:
  - Event 1: `GENERATE_THESIS` $\rightarrow$ Khởi tạo `THESIS-NVDA-001` (strength: 0.75, status: ACTIVE).
  - Event 2: `UPDATE_THESIS` $\rightarrow$ Củng cố CapEx, nâng strength lên 0.85.
  - Event 3: `UPDATE_THESIS` $\rightarrow$ Bổ sung rủi ro nghẽn đóng gói (counter-evidence), hạ strength xuống 0.70.
  - Event 4: `UPDATE_THESIS` $\rightarrow$ Vi phạm giả định cốt lõi số 1 và 3, chuyển trạng thái sang `KILLED` (strength: 0.0, có `kill_reason` chi tiết).
  - Event 5: `IGNORE` $\rightarrow$ Nhận diện tin PR/trao học bổng, bỏ qua không tác động state.

---

## 2. Chi Tiết Cấu Trúc Thư Mục Chuẩn Hóa

```text
gambling-change-your-life/
├── app/
│   ├── __init__.py
│   └── cli.py                       # CLI entry point
├── documents/
│   ├── finance_bootcamp.md          # Tài liệu tài chính nền tảng
│   ├── planning.md                  # Kiến trúc tổng thể MVP
│   ├── temp.md                      # Câu hỏi thiết kế & pipeline
│   ├── analysis_layer_spec.md       # Đặc tả kỹ thuật Analysis Layer
│   └── implementation_log.md        # File nhật ký triển khai này
├── domain/
│   ├── exceptions.py
│   ├── models/                      # Eric's models
│   │   ├── analyse_layer.py
│   │   ├── feedback.py
│   │   ├── research_layer.py
│   │   └── session.py
│   ├── schema/                      # [CHUẨN] Thư mục Schema phân lớp
│   │   ├── __init__.py
│   │   ├── event.py                 # Event, DecomposedEventItem, EventDecompositionOutput
│   │   ├── thesis.py                # Thesis, EvidenceItem, ThesisStatus
│   │   └── router.py                # RouterAction, RouterDecision, LLM outputs
│   └── prompts/                     # [CHUẨN] Thư mục Prompt chuyên biệt
│       ├── analyse.txt              # Eric's prompt
│       ├── research.txt             # Eric's prompt
│       ├── router.txt               # Prompt cho Router
│       ├── generate_thesis.txt      # Prompt tạo Thesis mới
│       ├── update_kill_thesis.txt   # Prompt cập nhật & Kill Thesis
│       └── decompose_event.txt      # Prompt bóc tách bản tin phức hợp
├── infra/
│   ├── llm/
│   │   ├── __init__.py              # Factory get_llm_client()
│   │   ├── mock.py                  # MockLLMClient (1 hàm generate_response)
│   │   └── openai.py                # OpenAIClient (1 hàm generate_response với instructor)
│   └── storage/
├── service/
│   ├── agents/
│   │   └── __init__.py              # Để trống theo chuẩn origin/thuan
│   ├── pipelines/
│   │   ├── __init__.py              # Export EventLayer, AnalysisLayer
│   │   ├── orchestration.py         # Orchestration pipeline kết nối hệ thống
│   │   └── layers/                  # [CHUẨN] Thư mục chứa các Layer độc lập
│   │       ├── __init__.py
│   │       ├── event_layer.py       # Class EventLayer (intake, validate, decompose)
│   │       └── analysis_layer.py    # Class AnalysisLayer (route, thesis lifecycle, state)
│   ├── shared/
│   │   ├── __init__.py
│   │   └── prompt_renderer.py       # Đọc và render prompt từ domain/prompts/
│   └── tools/
│       └── web_tool.py
├── tests/
│   ├── sample_events.json           # 5 Event mẫu chuẩn hóa 2 chiều
│   └── test_pipeline.py             # Test runner tự động xác nhận DoD
└── requirements.txt
```

---

## 3. Cách Kết Nối Orchestration

Người viết Orchestration dễ dàng kết nối các layer với cú pháp ngắn gọn:

```python
from infra.llm import get_llm_client
from service.pipelines.layers import AnalysisLayer, EventLayer

llm = get_llm_client()
event_layer = EventLayer(llm_client=llm)
analysis_layer = AnalysisLayer(llm_client=llm)

events = event_layer.process(raw_news_data)
for event in events:
    decision, thesis = analysis_layer.process_event(event)
```

---

## 4. Hướng Dẫn Chạy Kiểm Thử

```bash
cd /home/lftroq/project/gambling-change-your-life
./.venv/bin/python tests/test_pipeline.py
```
