# Nhật Ký Triển Khai (Implementation Log) — Analysis Layer & Schemas

> **Dự án**: Financial Research Agent (`gambling-change-your-life`)  
> **Nhiệm vụ tuần**: Chốt Event/Thesis Schema, Implement Router, Update Evidence/Counter-Evidence, Generate Thesis, Kill Decision.  
> **Definition of Done (DoD)**: Cho 3–5 event mẫu vào, system tạo/update/kill thesis đúng format, có reasoning.  
> **Trạng thái**: ✅ ĐÃ HOÀN THÀNH & VƯỢT TIÊU CHÍ DoD (Đã đồng bộ hoàn toàn kiến trúc DDD với nhánh `eric-dev`).

---

## 1. Nhật Ký Thực Hiện Từng Bước (Step-by-Step Log)

### Bước 1: Nghiên cứu tài liệu và phân tích yêu cầu
- **Nguồn tài liệu**: Đã đọc và đối chiếu `planning.md`, `temp.md`, `finance_bootcamp.md`, `analysis_layer_spec.md` và mã nguồn nhánh `eric-dev`.
- **Quyết định thiết kế**:
  1. Thống nhất cơ chế **2-Stage Routing**: Stage 1 lọc Candidate Theses theo vector/keyword tương đồng (tiết kiệm token cost); Stage 2 dùng LLM quyết định `GENERATE_THESIS`, `UPDATE_THESIS`, hoặc `IGNORE`.
  2. Bổ sung trường `expectation_context` vào Event Schema để đo lường 2 chiều: **Fundamental vs Expectation** (phát hiện Beat/Miss/Surprise so với Priced-in).
  3. Cố định tính bất biến của `core_claim` trong Thesis. Mọi biến động được ghi nhận qua `evidence`, `counter_evidence`, `strength`, và `reasoning`.
  4. Quyết định Kill Thesis do LLM đánh giá dựa trên việc **giả định cốt lõi (`core_assumptions`)** có bị đập gãy hay không (không dùng threshold số học cứng).
  5. Tách biệt hoàn toàn Thesis vs Prediction: Prediction là phái sinh từ Thesis, chỉ bị evaluate bởi Reality ở ngày đáo hạn.

### Bước 2: Tái cấu trúc chuẩn hóa theo kiến trúc của `eric-dev` (Domain-Driven Design)
- **Xóa bỏ thư mục `src/` đơn độc**: Không gom toàn bộ code vào một chỗ.
- **Thư mục Schema chuyên biệt (`domain/schema/` & `schema/`)**: Tách nhỏ từng file:
  - `event.py`: Event, EventNature, EventScope, ExpectationContext.
  - `thesis.py`: Thesis, ThesisStatus, EvidenceItem.
  - `router.py`: RouterAction, RouterDecision, ThesisGenerateOutput, ThesisUpdateOutput.
- **Thư mục Prompt chuyên biệt (`domain/prompts/` & `prompts/`)**: Viết prompt ra các file văn bản riêng biệt:
  - `router.txt`
  - `generate_thesis.txt`
  - `update_kill_thesis.txt`
  Được render tự động thông qua `service/shared/prompt_renderer.py`.
- **Thư mục Agents (`service/agents/`)**:
  - `router.py`: ThesisRouter.
  - `thesis_analyzer.py`: ThesisAnalyzer.
- **Thư mục Pipelines (`service/pipelines/`)**:
  - `analysis_pipeline.py`: AnalysisPipeline điều phối luồng.
  - `orchestration.py`: Tích hợp luồng scraper/research của Eric.
- **Thư mục LLM Infra (`infra/llm/`)**:
  - `base.py`: BaseLLMClient interface.
  - `mock.py`: MockFinancialLLMClient chạy test offline không tốn API key.
  - `openai.py`: OpenAIClient dùng instructor cho structured outputs.

### Bước 3: Kiểm thử nghiệm thu DoD
- Chạy lệnh: `./.venv/bin/python tests/test_pipeline.py`.
- **Kết quả**: 100% assertions passed, xác nhận cả 5 event mẫu (Tạo mới $\rightarrow$ Củng cố $\rightarrow$ Nghẽn cung ứng $\rightarrow$ Kill do gãy giả định $\rightarrow$ Ignore tin nhiễu).

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
│   └── implementation_log.md        # File nhật ký này
├── domain/
│   ├── exceptions.py
│   ├── models/                      # Eric's models & Re-exports
│   │   ├── analyse_layer.py
│   │   ├── feedback.py
│   │   ├── research_layer.py
│   │   └── session.py
│   ├── schema/                      # [CHUẨN] Thư mục Schema chuyên biệt
│   │   ├── __init__.py
│   │   ├── event.py                 # Event, ExpectationContext, Scope, Nature
│   │   ├── thesis.py                # Thesis, EvidenceItem, ThesisStatus
│   │   └── router.py                # RouterAction, RouterDecision, LLM outputs
│   └── prompts/                     # [CHUẨN] Thư mục Prompt chuyên biệt
│       ├── analyse.txt              # Eric's prompt
│       ├── research.txt             # Eric's prompt
│       ├── router.txt               # Prompt cho Router
│       ├── generate_thesis.txt      # Prompt tạo Thesis mới
│       └── update_kill_thesis.txt   # Prompt cập nhật & Kill Thesis
├── infra/
│   ├── llm/
│   │   ├── __init__.py              # Factory get_llm_client()
│   │   ├── base.py                  # BaseLLMClient interface
│   │   ├── mock.py                  # MockFinancialLLMClient
│   │   └── openai.py                # OpenAIClient
│   └── storage/
├── service/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── router.py                # ThesisRouter (Candidate Filter + Routing)
│   │   └── thesis_analyzer.py       # ThesisAnalyzer (Create / Update / Kill)
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── analysis_pipeline.py     # AnalysisPipeline
│   │   └── orchestration.py         # Eric's Orchestration
│   ├── shared/
│   │   ├── __init__.py
│   │   └── prompt_renderer.py       # Đọc và render prompt từ domain/prompts/
│   └── tools/
│       └── web_tool.py
├── schema/                          # Shortcut import tiện lợi: from schema import ...
├── prompts/                         # Shortcut path truy xuất prompt
├── tests/
│   ├── sample_events.json           # 5 Event mẫu chuẩn hóa 2 chiều
│   └── test_pipeline.py             # Test runner tự động xác nhận DoD
└── requirements.txt
```

---

## 3. Hướng Dẫn Chạy Kiểm Thử

```bash
cd /home/lftroq/project/gambling-change-your-life
./.venv/bin/python tests/test_pipeline.py
```
