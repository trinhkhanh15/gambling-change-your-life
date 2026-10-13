# Chạy và đọc log của Financial Agent

## Mục tiêu

Đây là project học cách dựng một agent theo pipeline và kiểm tra feedback loop
trên dữ liệu lịch sử. Nó **không phải công cụ giao dịch**. Điểm trong log là tín
hiệu chẩn đoán pipeline, không chứng minh agent dự báo thị trường chính xác.

## Chạy replay

Chuẩn bị một CSV gộp các event muốn chạy. Dữ liệu collector hiện được chia theo
tháng/domain; khi gộp, giữ cột `domain` để biết event thuộc nhóm nào. CSV cần có
các cột `published_at,title,content,source,domain`. Bảng ticker cần có
`ticker,company,domain,currency`.

Từ thư mục gốc của repo, chọn khoảng ngày event muốn replay:

```bash
python -m app.e2e \
  --events data/events.csv \
  --tickers data/stock_tickers.csv \
  --start-date 2025-01-01 \
  --end-date 2025-03-31 \
  --data-dir data_storage/replays/q1-mock
```

Mặc định CLI dùng `MockLLMClient` xác định để chạy nhanh và không gọi dịch vụ
bên ngoài. Muốn dùng OpenAI, đặt `OPENAI_API_KEY` rồi thêm `--openai`:

```bash
python -m app.e2e \
  --events data/events.csv \
  --tickers data/stock_tickers.csv \
  --start-date 2025-01-01 \
  --end-date 2025-03-31 \
  --data-dir data_storage/replays/q1-openai \
  --openai
```

CLI hiện dùng model mặc định `gpt-5.4-mini` khi bật `--openai`. Mỗi lần chạy
nên dùng `--data-dir` riêng nếu muốn so sánh các run; nếu dùng lại thư mục,
thesis, prediction và evaluation cũ vẫn nằm trong JSON repository và có thể
được đưa vào feedback của event sau.

`--start-date` và `--end-date` lọc ngày đăng event theo UTC và bao gồm cả hai
đầu mút. CSV giá luôn lấy từ `data/market/stock_prices_daily.csv`, không bị cắt
theo khoảng event: cần giá trước ngày bắt đầu để làm baseline và các phiên sau
event cuối để resolve horizon. Nếu CSV giá thiếu các ngày đó, prediction có thể
chưa được đánh giá trong run.

## Thu thập news/report data

Script từ branch `eric-dev` là `scripts/collect_data.py`. Nó tìm bài qua Google
News RSS, giải mã publisher URL, trích nội dung bài và ghi CSV theo tháng/chủ đề.
Các khoảng ngày và chủ đề nằm ở đầu script; mặc định output là
`data/raw_news_websearch/`. Script nhắm tới 3 bài/ngày, in tiến độ và lưu ngày
không đủ bài vào `shortfalls.csv`.

Cài dependencies và chạy từ repo root:

```bash
python -m pip install -r requirements.txt
python scripts/collect_data.py
```

Lệnh này truy cập Google News và publisher websites, chạy nhiều tháng song
song, nên có thể tạo nhiều request và mất thời gian. Không chạy lại chỉ để xem
CLI replay; để đọc data có sẵn thì chạy `python -m app.e2e` ở phần trên.

### Tham số chính

| Tham số | Ý nghĩa |
| --- | --- |
| `--events` | Một file CSV event duy nhất; cần `published_at,title,content,source,domain`. |
| `--tickers` | File CSV ticker/company; cần `ticker,company,domain,currency`. |
| `--start-date` | Ngày event đầu tiên, định dạng `YYYY-MM-DD`, tính theo UTC và được bao gồm. |
| `--end-date` | Ngày event cuối cùng, định dạng `YYYY-MM-DD`, tính theo UTC và được bao gồm. |
| `--data-dir` | Thư mục chứa `records.json`; dữ liệu tồn tại ở đây được nạp lại cho run sau. |
| `--openai` | Dùng `OpenAIAdapter`; nếu không có cờ này, dùng mock xác định. |

Giá luôn đọc từ `data/market/stock_prices_daily.csv`. CLI xử lý tất cả event
trong khoảng ngày, không giới hạn số dòng ngầm định.

## Luồng chạy

```text
News CSV
   ↓ lọc ngày, bỏ dòng lỗi/duplicate, nhận diện company tags, sort theo thời gian
Event
   ↓ router: IGNORE / GENERATE_THESIS / UPDATE_THESIS
Thesis
   ↓ tạo prediction nếu thesis còn active và có market window
Prediction
   ↓ chờ horizon đến hạn, tra adjusted close (fallback close)
Reality
   ↓ so prediction với reality
Evaluation
   ↓ chỉ feedback đã observed trước event mới được thêm vào prompt sau
Event tiếp theo
```

Pipeline chạy tuần tự theo `published_at`. Trước khi phân tích một event, các
prediction đã đến hạn được resolve. Sau khi xử lý xong toàn bộ event, pipeline
thử resolve các prediction còn active tới ngày giá mới nhất trong CSV.

## Đọc trace trong terminal

Mỗi run bắt đầu bằng cấu hình: LLM/provider, file đầu vào, khoảng ngày và nơi
lưu records. Đối chiếu phần này trước khi so hai run để biết chúng có dùng cùng
model, dữ liệu và storage hay không.

Mỗi block `[n] EVENT` in ra:

1. **EVENT** — ID ổn định, ngày đăng, nguồn, tiêu đề và company tags được CSV
   adapter nhận diện.
2. **ROUTER** — action, thesis đích và reasoning do LLM trả về.
3. **THESIS** — ticker, trạng thái, strength, claim, reasoning và evidence/counter-
   evidence được thêm từ đúng event này. Cảnh báo ticker nghĩa là ticker thesis
   không nằm trong các company tags phát hiện từ event; đây là tín hiệu để người
   đọc kiểm tra, chưa phải kết luận router chắc chắn sai. Nếu event có nhiều
   ticker được phát hiện, log nhắc kiểm tra vì tag có mặt chưa chứng minh đó là
   công ty trung tâm của tin.
4. **PREDICTION** — target, chiều, mức thay đổi kỳ vọng, confidence, baseline,
   ngày bắt đầu/kết thúc horizon, cutoff thông tin và drivers. Nếu không tạo được
   prediction, log nêu lý do pipeline biết được.
5. **EVALUATION** — actual move và điểm direction, magnitude, drivers, matching
   khi đã có evaluation. `not assessed` ở drivers nghĩa là reality chưa có
   actual drivers để so sánh. Nếu outcome được quan sát sau ngày event, log ghi
   rõ ngày resolve; đây là kết quả đến sau, không phải feedback có sẵn lúc
   event được phân tích. Evaluation của prediction được nhiều event dùng lại chỉ
   in một lần trong replay.

Cảnh báo horizon trên 10 ngày lịch yêu cầu kiểm tra coverage của ngày giao dịch.
Nó không tự kết luận dữ liệu sai: ngày nghỉ có thể làm số ngày lịch dài hơn.
Khi không tạo prediction, log cho biết target không map được, không có baseline
trước event, hay chưa đủ số row giá sau baseline. Khi chưa có evaluation, log
phân biệt đang chờ horizon với trường hợp horizon đã qua nhưng thiếu row giá
đúng ngày.

Cuối run, summary phân biệt số prediction duy nhất được tham chiếu, prediction
mới tạo, evaluation vừa tạo và evaluation gắn với replay. Một prediction có thể
được nhiều event sau tham chiếu lại trong lúc nó còn active, nên đếm event có
prediction không đồng nghĩa với số prediction duy nhất.

`matching_score` là metric nội bộ hiện tại: direction và magnitude mỗi phần
đóng góp 40%, drivers đóng góp 20% nếu có actual drivers. Không diễn giải điểm
này như accuracy, lợi nhuận hay so sánh công bằng giữa các ticker.

Run trả mã `0` khi replay có prediction và evaluation được liên kết; mã `2` khi
chưa đạt cả hai điều kiện. Ví dụ replay bắt đầu đúng ngày đầu tiên có giá có
thể chưa có baseline và vì vậy chưa tạo được prediction.

## Giới hạn đã biết cần giữ trong đầu

- Company tags là nhận diện theo chuỗi tên/ticker trong nội dung; không phải
  entity resolution hiểu ngữ cảnh.
- Resolver hiện chọn row giá thứ năm sau baseline theo thứ tự các row có sẵn.
  Nếu file thiếu ngày giao dịch, horizon thực tế có thể dài hơn năm phiên.
- Thesis routing có thể gom event khác công ty vào cùng thesis. Hãy xem warning
  và evidence từng event trước khi dùng điểm evaluation để kết luận.
- CSV giá hiện không cung cấp actual drivers, nên thành phần drivers thường là
  `not assessed`.
- Chọn khoảng ngày dài làm run lâu và tốn API hơn khi dùng OpenAI; mỗi event có
  thể phát sinh nhiều lời gọi LLM.

## Thứ tự học/đọc code

1. `app/e2e.py` — cấu hình CLI, dựng adapters, in trace và summary.
2. `infra/sources/csv_events.py` — CSV được chuyển thành `Event` thế nào.
3. `service/pipelines/pipeline.py` — thứ tự xử lý, chờ resolve và feedback.
4. `service/pipelines/layers/analysis_layer.py` — routing và cập nhật thesis.
5. `service/pipelines/layers/prediction_layer.py` — tạo prediction.
6. `infra/sources/stock_prices.py` và `service/pipelines/layers/evaluation_layer.py`
   — reality và score được tạo thế nào.

Đọc log trước, chọn một lỗi có thể quan sát, viết một giả thuyết tối ưu, rồi
thiết kế lần chạy kế tiếp sao cho chỉ thay đổi điều cần kiểm tra.
