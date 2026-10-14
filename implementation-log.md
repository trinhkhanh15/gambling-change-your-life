# Implementation Log: End-to-End Pipeline & Real LLM Integration

**Date**: 2026-10-14  
**Author**: lftroq  
**Branch**: `lftroq-dev` (synced with `develop`)  
**Scope**: Tích hợp mô hình LLM thực tế (`gpt-5.6-luna`), sửa lỗi dữ liệu, tối ưu hóa I/O và khống chế danh mục mã cổ phiếu cho quy trình Replay sự kiện tài chính/thị trường.

---

## 1. Bối cảnh & Mục tiêu

Quy trình End-to-End (`app/e2e.py`) thực hiện mô phỏng luồng phát hiện sự kiện tin tức, phân tích tạo/cập nhật luận điểm (`Thesis`), đưa ra dự đoán giá cổ phiếu (`Prediction`), lấy giá thực tế từ thị trường (`Reality`) và chấm điểm đánh giá (`Evaluation`).

Trước khi triển khai, hệ thống chỉ chạy thử nghiệm với `MockLLMClient`. Khi đưa vào chạy thực tế với dữ liệu tin tức tài chính Q1-Q2/2025 và LLM thật từ OpenAI, dự án gặp phải các vấn đề kỹ thuật:
1. **Lỗi tràn bộ đệm CSV**: Các bài báo dài trong cột `content` vượt quá giới hạn 128KB mặc định của Python `csv`.
2. **Hiệu năng I/O nghẽn nghiêm trọng**: `JsonRepository` đọc/ghi toàn bộ file `records.json` từ đĩa và gọi `os.fsync` ở mỗi sự kiện, khiến mock run 270 sự kiện mất hơn 2 phút 20 giây.
3. **Mã Ticker ngoại lai & không khớp giá**: LLM tự chọn quỹ ETF ngành (như `XLU`) thay vì chọn cổ phiếu doanh nghiệp trong danh mục theo dõi (`data/stock_tickers.csv`), khiến khâu dự đoán bị bỏ qua (`incomplete (exit 2)`).
4. **Sai lệch đơn vị phần trăm dự đoán**: LLM trả về số nguyên `3.0` (cho 3%), dẫn đến dự báo bị format thành `+300.00%` và làm sai lệch điểm `magnitude_score`.
5. **Cấu hình mô hình `gpt-5.6-luna`**: Mô hình reasoning mới đòi hỏi thiết lập `reasoning_effort="none"` khi dùng structured outputs qua function calling.

---

## 2. Chi tiết các thay đổi & Cải tiến kỹ thuật

### 2.1. Khắc phục lỗi đọc bài báo dài (`csv.field_size_limit`)
- **Tệp thay đổi**:
  - [`infra/sources/csv_events.py`](file:///home/lftroq/project/gambling-change-your-life/infra/sources/csv_events.py)
  - [`app/e2e.py`](file:///home/lftroq/project/gambling-change-your-life/app/e2e.py)
- **Giải pháp**: Bổ sung `csv.field_size_limit(sys.maxsize)` ở đầu tệp để hỗ trợ các bài báo có độ dài lớn trong tập dữ liệu `2025-Q1.csv` và `2025-Q2.csv`.

### 2.2. Tối ưu hóa I/O bộ lưu trữ JSON (`JsonRepository`)
- **Tệp thay đổi**:
  - [`infra/storage/json_repository.py`](file:///home/lftroq/project/gambling-change-your-life/infra/storage/json_repository.py)
- **Vấn đề**: Trước đây, mỗi lần gọi `save()`, `get()`, `list()`, code đều đọc toàn bộ file `records.json` từ ổ cứng, parse JSON, và ghi xuống đĩa kèm hàm `os.fsync` (chặn I/O đĩa vật lý). Với 270 sự kiện, số lượng thao tác I/O lặp lại lên tới hàng chục nghìn lần.
- **Giải pháp**:
  - Thêm bộ đệm trong bộ nhớ RAM (`self._cache`).
  - Kiểm tra thời gian sửa đổi file (`st_mtime_ns`) trước khi đọc từ đĩa; nếu file chưa bị thay đổi bởi tiến trình bên ngoài, trả về dữ liệu trong RAM ngay lập tức ($O(1)$).
  - Loại bỏ `os.fsync` gây nghẽn đĩa; duy trì tính nguyên tử bằng cách ghi file tạm và `os.replace`.
- **Kết quả đo lường (Benchmark toàn bộ 270 sự kiện Q1)**:
  - Trước tối ưu: `2m 20.98s` (trong đó thời gian CPU hệ thống `sys` chiếm `43.4s`).
  - Sau tối ưu: **`29.78s`** (thời gian `sys` giảm xuống chỉ còn `1.2s`).
  - **Tốc độ nhanh gấp gần 5 lần!**

### 2.3. Hỗ trợ Model `gpt-5.6-luna` & Cấu hình Reasoning
- **Tệp thay đổi**:
  - [`infra/llm/openai_adapter.py`](file:///home/lftroq/project/gambling-change-your-life/infra/llm/openai_adapter.py)
  - [`app/e2e.py`](file:///home/lftroq/project/gambling-change-your-life/app/e2e.py)
- **Giải pháp**:
  - Thiết lập `reasoning_effort="none"` cho các mô hình dòng reasoning/luna khi gọi structured output qua `instructor`.
  - Đổi model mặc định thành `gpt-5.6-luna` (thời gian phản hồi đo được chỉ ~1.3s/lần gọi, nhanh gấp đôi so với `gpt-5.4-mini`).
  - Thêm tham số CLI `--model` vào `app/e2e.py` để tùy chọn model linh hoạt.

### 2.4. Ràng buộc Ticker hợp lệ (`valid_tickers`)
- **Tệp thay đổi**:
  - [`service/pipelines/layers/analysis_layer.py`](file:///home/lftroq/project/gambling-change-your-life/service/pipelines/layers/analysis_layer.py)
  - [`app/e2e.py`](file:///home/lftroq/project/gambling-change-your-life/app/e2e.py)
- **Giải pháp**:
  - Nạp 46 mã cổ phiếu doanh nghiệp hợp lệ từ [`data/stock_tickers.csv`](file:///home/lftroq/project/gambling-change-your-life/data/stock_tickers.csv).
  - Đưa ràng buộc nghiêm ngặt vào system prompt của `AnalysisLayer.generate_thesis`: Bắt buộc chọn một mã cổ phiếu doanh nghiệp chịu tác động trực tiếp nhất từ danh sách, cấm dùng ETF (như `XLU`, `SPY`) hoặc mã nằm ngoài danh mục.
  - Chuẩn hóa chuỗi ticker trả về (loại bỏ ký tự lạ, chuyển chữ hoa) để đảm bảo khớp dữ liệu giá.

### 2.5. Chuẩn hóa tỷ lệ phần trăm dự đoán (`expected_change_pct`)
- **Tệp thay đổi**:
  - [`service/pipelines/layers/prediction_layer.py`](file:///home/lftroq/project/gambling-change-your-life/service/pipelines/layers/prediction_layer.py)
- **Giải pháp**:
  - Bổ sung hướng dẫn rõ ràng trong prompt yêu cầu trả về số thập phân (ví dụ `0.03` cho +3%).
  - Bổ sung logic tự động chuẩn hóa: nếu `abs(expected_change_pct) >= 1.0`, tự động chia cho 100 để tránh lỗi phóng đại 100 lần khi format hiển thị và tính điểm `magnitude_score`.

### 2.6. Quản lý Môi trường & Dependency
- Cập nhật [`requirements.txt`](file:///home/lftroq/project/gambling-change-your-life/requirements.txt): Bổ sung `python-dotenv>=1.0.0` và `pytest>=8.0.0`.
- Cập nhật [`.gitignore`](file:///home/lftroq/project/gambling-change-your-life/.gitignore): Bổ sung thư mục đầu ra `data_storage/` và tệp cấu hình `.env`.
- Cập nhật [`app/e2e.py`](file:///home/lftroq/project/gambling-change-your-life/app/e2e.py): Tự động nạp `.env` qua `load_dotenv()`.

---

## 3. Kết quả Kiểm thử & Đánh giá (Verification)

### 3.1. Unit & Integration Tests
Chạy toàn bộ test suite:
```bash
PYTHONPATH=. ./.venv/bin/pytest tests/
```
- **Kết quả**: `6 passed in 0.30s` (toàn bộ kiểm thử luồng nội bộ và mock CSV đều pass).

### 3.2. Chạy thử nghiệm thực tế với LLM `gpt-5.6-luna` (5 ngày đầu Q1)
Chạy lệnh:
```bash
./.venv/bin/python -m app.e2e \
  --events data/events_by_quarter/2025-Q1.csv \
  --tickers data/stock_tickers.csv \
  --start-date 2025-01-01 \
  --end-date 2025-01-05 \
  --data-dir data_storage/replays/test-luna \
  --openai \
  --model gpt-5.6-luna
```
- **Kết quả thực thi**:
  - Đã xử lý: 15 sự kiện tin tức.
  - Tác vụ Router: `{'GENERATE_THESIS': 1, 'IGNORE': 9, 'UPDATE_THESIS': 5}`.
  - Luận điểm tạo ra: Gán chính xác cho mã **`EQIX` (Equinix)** về ảnh hưởng cạnh tranh và năng lượng từ việc DayOne gọi vốn $1.9B mở rộng trung tâm dữ liệu.
  - Dự đoán thị trường: Xác định giá cơ sở $909.19 ngày 02/01/2025 cho `EQIX` và horizon ngày 10/01/2025.
  - Đánh giá kết quả (`Evaluation`): Đối chiếu thành công với giá thực tế ngày 10/01 ($866.44).
  - Trạng thái kết thúc: **`E2E completion: passed (exit 0)`**.

---

## 4. Hướng dẫn sử dụng cho Teammate

1. **Cài đặt thư viện**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Cấu hình API Key**:
   Tạo file `.env` tại thư mục gốc với nội dung:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. **Chạy Replay toàn bộ Quý 1/2025**:
   ```bash
   python -m app.e2e \
     --events data/events_by_quarter/2025-Q1.csv \
     --tickers data/stock_tickers.csv \
     --start-date 2025-01-01 \
     --end-date 2025-03-31 \
     --data-dir data_storage/replays/q1_luna \
     --openai \
     --model gpt-5.6-luna
   ```
4. **Chạy Replay toàn bộ Quý 2/2025**:
   ```bash
   python -m app.e2e \
     --events data/events_by_quarter/2025-Q2.csv \
     --tickers data/stock_tickers.csv \
     --start-date 2025-04-01 \
     --end-date 2025-06-30 \
     --data-dir data_storage/replays/q2_luna \
     --openai \
     --model gpt-5.6-luna
   ```
