# Finance cho project AI Hypothesis Agent

Bây không cần học hết finance.

Mục tiêu của đống này chỉ là: **đọc được một công ty đang làm gì, một cái news/report vừa thay đổi điều gì, rồi từ đó tạo ra một hypothesis có lý để đem đi kiểm chứng sau.**

Nếu học xong mà ae biết một đống định nghĩa nhưng nhìn earnings report vẫn đéo biết chuyện gì đang xảy ra thì coi như học sai hướng.

---

# Outcome cuối cùng

Sau khi học xong phần finance cơ bản này, bây nên làm được kiểu như vầy:

```text
Company: NVIDIA

Có chuyện gì:
Revenue data center tăng mạnh, guidance tiếp tục được nâng.

T đang nghĩ gì:
Demand cho AI infrastructure vẫn mạnh hơn market đang kỳ vọng.

Evidence:
- Data center revenue tăng mạnh.
- Hyperscaler vẫn tăng CapEx.
- Management nâng guidance.

Nhưng có gì chống lại hypothesis này:
- Valuation đã rất cao.
- Gross margin guidance giảm.
- Một phần growth có thể đã được price in.

Prediction:
Bullish relative to semiconductor sector trong 1–5 ngày.

Confidence:
0.68
```

Không cần đúng.

Cái cần là **anh em biết tại sao mình nghĩ như vậy, evidence nằm đâu, và sau này có data để biết mình sai ở đâu.**

---

# 1. Trước hết: công ty kiếm tiền kiểu gì?

Đây là thứ đầu tiên t sẽ nhìn khi đọc một công ty.

Nghe đơn giản nhưng nếu bây không hiểu business thì mấy con số phía sau gần như vô nghĩa.

Ví dụ Spotify.

Nó có hai nguồn tiền lớn:

- subscription
- advertising

Nếu số user tăng nhưng phần lớn là free user thì revenue chưa chắc tăng mạnh.

Nếu Premium subscribers tăng thì ngon hơn.

Nếu Spotify tăng giá subscription thì revenue/user có thể tăng, nhưng đổi lại user có thể cancel nhiều hơn.

Nghĩa là khi đọc:

> Spotify revenue tăng 15%

đừng dừng ở đó.

Câu đáng hỏi hơn là:

> **Tại sao nó tăng?**

Do:

- user tăng?
- giá tăng?
- khách trả tiền nhiều hơn?
- acquisition?
- exchange rate?
- một segment nào đó tăng bất thường?

Tương tự với NVIDIA.

NVIDIA kiếm tiền từ nhiều mảng, nhưng hiện tại Data Center là cực kỳ quan trọng.

Nếu gaming tăng 10% và Data Center giảm 20%, headline "một số segment vẫn tăng" chẳng cứu được thesis nhiều đâu.

## Mấy thứ cần biết

- Revenue
- Revenue Growth
- Business Segment
- Customer
- Pricing
- Volume / Units Sold
- Recurring Revenue
- One-time Revenue

Không cần thuộc định nghĩa sách giáo khoa.

Chỉ cần nhìn vào business rồi hiểu:

> **tiền đang chảy vào từ đâu.**

---

# 2. Revenue không phải profit

Một công ty bán được nhiều hơn chưa chắc kiếm được nhiều tiền hơn.

Ví dụ:

```text
Revenue năm trước: $100
Cost: $60
Profit trước operating expenses: $40
```

Năm nay:

```text
Revenue: $120
Cost: $90
Profit trước operating expenses: $30
```

Revenue tăng 20%.

Nhìn qua tưởng ngon.

Nhưng tiền kiếm được sau cost lại giảm.

Đó là lý do margin quan trọng.

## Gross Margin

```text
Gross Margin = Gross Profit / Revenue
```

Nó cho ae intuition kiểu:

> Với mỗi $1 bán được, còn lại bao nhiêu sau cost trực tiếp để tạo ra sản phẩm/dịch vụ đó?

Ví dụ một software company thường có gross margin rất cao vì bán thêm một software license không tốn nhiều tiền để "sản xuất".

Một retailer thì khác.

Muốn bán thêm một cái áo, nó phải mua/sản xuất thêm một cái áo.

---

# 3. Mấy tầng profit cơ bản

Không cần học accounting sâu.

Anh em chỉ cần hiểu dòng tiền đại khái đi qua như này:

```text
Revenue
↓
trừ cost để tạo ra sản phẩm
↓
Gross Profit
↓
trừ R&D, Sales, Marketing, nhân viên, văn phòng...
↓
Operating Income
↓
trừ thêm interest, tax và vài thứ khác
↓
Net Income
```

Mấy từ bây nên nhận ra khi đọc report:

- Revenue
- Cost of Revenue / COGS
- Gross Profit
- Gross Margin
- Operating Expenses
- R&D
- Sales & Marketing
- Operating Income
- Operating Margin
- Net Income
- EPS

Không cần memorize formula từng cái.

Quan trọng là nhìn ra chuyện kiểu:

> Revenue tăng mà operating income giảm.

Thì biết rằng **đâu đó ở giữa đang có vấn đề**.

Có thể company đang:

- đốt nhiều tiền cho R&D
- hiring mạnh
- discount sản phẩm
- cost đầu vào tăng
- margin giảm
- scale chưa hiệu quả

---

# 4. Profit cũng chưa chắc là cash

Đây là đoạn hơi accounting một tí nhưng khá quan trọng.

Company có thể report profit nhưng cash thực tế không tăng tương ứng.

Ví dụ công ty bán hàng cho khách:

> "Mua trước đi, 3 tháng nữa trả tiền."

Accounting có thể ghi nhận revenue trước khi cash thật sự về tài khoản.

Hoặc company đang kiếm được profit nhưng phải đổ cực nhiều tiền vào nhà máy, server, chip, máy móc.

Thế nên ae nên biết:

- Operating Cash Flow
- CapEx
- Free Cash Flow

Một approximation đơn giản:

```text
Free Cash Flow
≈
Operating Cash Flow - CapEx
```

T không cần bây trở thành accountant.

Chỉ cần hiểu:

> **Net income là câu chuyện kế toán. Cash là tiền thật đang chảy. Hai thứ liên quan nhưng không phải một.**

---

# 5. Ba cái financial statement là gì?

Đọc report sẽ gặp ba thằng này suốt.

## Income Statement

Nó kể câu chuyện:

> Trong một khoảng thời gian, company bán được bao nhiêu và lời lỗ ra sao?

Thường nhìn:

- Revenue
- Gross Profit
- Operating Income
- Net Income
- EPS

## Balance Sheet

Nó giống một tấm hình chụp company tại một thời điểm.

Nó cho bây thấy:

- Cash
- Assets
- Inventory
- Debt
- Liabilities
- Equity

Ví dụ inventory tăng rất nhanh nhưng sales không tăng tương ứng.

Có thể là:

> hàng đang chất kho vì demand yếu.

Không phải lúc nào cũng vậy, nhưng đó là một hypothesis đáng kiểm tra.

## Cash Flow Statement

Nó trả lời:

> Tiền thật đi đâu và từ đâu tới?

Biết ba nhóm:

- Operating Cash Flow
- Investing Cash Flow
- Financing Cash Flow

Đọc sơ được là đủ.

---

# 6. Growth: tăng bao nhiêu chưa đủ, phải biết tăng từ đâu

Ae sẽ gặp hai thứ này rất nhiều:

- YoY = Year over Year
- QoQ = Quarter over Quarter

Ví dụ:

```text
Q2 2025 revenue: $10B
Q2 2026 revenue: $12B
```

YoY growth:

```text
20%
```

Nhưng một lần nữa:

> 20% đó từ đâu ra?

Ví dụ Meta revenue tăng vì:

- số ad impressions tăng
- giá mỗi ad tăng
- engagement tăng

Một SaaS company có thể tăng do:

- customer mới
- customer cũ trả nhiều hơn
- churn giảm
- tăng giá

Hai công ty cùng +20% revenue nhưng quality của growth có thể rất khác nhau.

---

# 7. Stock là cái gì?

Cái này bây chỉ cần intuition.

Một share là một phần ownership trong company.

Company có:

```text
Shares Outstanding
```

Nếu:

```text
1B shares
```

và mỗi share giá:

```text
$100
```

thì:

```text
Market Cap = $100B
```

Formula:

```text
Market Cap = Share Price × Shares Outstanding
```

## IPO

IPO là lúc company đưa shares ra public market.

Sau đó phần lớn trading mà ae thấy mỗi ngày là investor mua bán shares với nhau trên **secondary market**.

Nghĩa là:

> Eric mua NVIDIA từ thằng A giá $100 rồi bán cho thằng B giá $110.

$10 chênh lệch đó không phải NVIDIA trả.

Đó chỉ là market định giá share khác đi.

---

# 8. Stock price thực tế chạy kiểu gì?

Ngắn gọn:

Có người muốn mua.

Có người muốn bán.

Họ đặt mức giá họ chấp nhận.

Anh em nên biết:

- Bid
- Ask
- Spread
- Order Book
- Liquidity

Không cần học market microstructure sâu.

Chỉ cần hiểu rằng stock price không phải một con số "company quyết định".

Nó là kết quả của trading giữa một đống người với expectation khác nhau.

---

# 9. Good company chưa chắc là good stock

Đây là một trong những ý quan trọng nhất.

Giả sử company A tuyệt vời.

Revenue tăng 50%.

Profit tăng 70%.

AI product bán như điên.

Nghe bullish vl.

Nhưng nếu trước earnings, market đã kỳ vọng:

```text
Revenue +80%
```

thì +50% lại là một disappointment.

Đây là lý do ae phải biết valuation và expectations.

---

# 10. Valuation

Bây chưa cần làm DCF ngay.

Trước mắt chỉ cần hiểu:

> Market đang trả bao nhiêu cho business này?

## P/E

Roughly:

```text
P/E = Price / Earnings
```

Nếu hai company kiếm cùng một lượng profit nhưng company A được market trả giá gấp đôi company B, A có valuation cao hơn.

Không có nghĩa A overpriced.

Có thể market nghĩ A sẽ grow nhanh hơn rất nhiều.

## P/S

```text
P/S = Market Cap / Revenue
```

Hay dùng với những company chưa có nhiều profit.

## EV/EBITDA

Biết tên và intuition là được.

Chưa cần đào sâu.

Ý quan trọng hơn mấy cái multiple:

> **Valuation là expectation được nhét vào price.**

Company càng được kỳ vọng nhiều thì càng khó tạo positive surprise.

---

# 11. Expectations mới là thứ cực quan trọng

Nếu ae chỉ nhớ một phần trong file này thì nhớ cái này.

Market không phản ứng đơn giản với:

```text
good news
bad news
```

Nó phản ứng với:

```text
what happened
vs
what people expected
```

Ví dụ:

Market nghĩ Tesla sẽ giao:

```text
500,000 cars
```

Actual:

```text
480,000
```

480k nghe rất lớn.

Nhưng so với expectation thì đó là miss.

Ngược lại:

Market nghĩ:

```text
400,000
```

Actual:

```text
480,000
```

Cùng một con số 480k, nhưng lần này là positive surprise.

Đó là lý do một news không có meaning tuyệt đối.

Meaning của nó phụ thuộc vào cái market đã tin trước đó.

---

# 12. Beat, miss, consensus

Khi đọc earnings bây sẽ thấy:

- Analyst Estimate
- Consensus Estimate
- Revenue Beat
- Revenue Miss
- EPS Beat
- EPS Miss

Ví dụ:

```text
Consensus EPS: $2.00
Actual EPS: $2.30
```

Company beat EPS estimate.

Nhưng đừng tự động conclude bullish.

Market có thể đang quan tâm một thứ khác hơn:

- future guidance
- margins
- user growth
- CapEx
- một segment quan trọng

---

# 13. Guidance

Guidance là management nói:

> Tụi t nghĩ quarter/năm tiếp theo sẽ trông như này.

Ví dụ company vừa report:

```text
Revenue: rất ngon
EPS: beat
```

nhưng management nói:

```text
Next quarter revenue expected to slow sharply.
```

Stock vẫn có thể dump.

Lý do khá đơn giản:

> Market mua future, không mua quá khứ.

Mấy loại guidance thường gặp:

- Revenue
- EPS
- Margin
- CapEx
- Units / Shipments
- User Growth

---

# 14. "Priced in" là gì?

Giả sử cả thế giới đã biết Apple sắp launch một iPhone mới cực ngon.

News launch xảy ra.

Có thể stock chẳng tăng gì.

Không phải vì event không tốt.

Mà vì:

> mọi người đã mua stock từ trước vì kỳ vọng event này rồi.

Price hiện tại đã phản ánh một phần expectation đó.

Đó là "priced in".

Một câu hỏi rất đáng hỏi khi đọc news:

> **Cái này thật sự mới hay market đã biết gần hết rồi?**

---

# 15. Những thứ có thể thay đổi một company

Không cần memorize hết.

## Company-specific

- Earnings
- Guidance
- Product launch
- Pricing
- Major contract
- Major customer win/loss
- Acquisition
- CEO / management change
- Layoffs
- Lawsuit
- Regulation
- Supply problem

## Industry

- Competitor launch sản phẩm
- Supply/demand
- Commodity/input costs
- New technology
- Industry regulation

## Macro

- Interest rates
- Inflation
- Recession / economic growth
- FX
- Employment

Macro thì học tới đâu cần tới đó.

Đừng lao vào học nguyên macroeconomics trước khi build.

---

# 16. Event có thể đi xuyên qua business như nào?

Ví dụ TSMC gặp vấn đề production.

Có thể story đi kiểu:

```text
Production issue
↓
wafer output giảm
↓
chip supply giảm
↓
shipments giảm
↓
revenue bị ảnh hưởng
```

Nhưng đôi khi:

```text
supply giảm
↓
price tăng
↓
margin lại tăng
```

Tức là một event có thể tạo ra nhiều effect cùng lúc.

Không cần ép mọi thứ vào một framework.

Chỉ cần tập nhìn:

> **Cái event này chạm vào phần nào của business?**

Rồi đi tiếp từ đó.

---

# 17. Luôn có counter-evidence

Nếu anh em tìm được một hypothesis rất đẹp mà toàn bộ evidence đều support nó thì nên nghi ngờ chính mình.

Ví dụ:

```text
Hypothesis:
AI chip demand sẽ tiếp tục cực mạnh.
```

Evidence:

- cloud companies tăng CapEx
- NVIDIA tăng guidance
- backlog lớn

Counter-evidence có thể là:

- customers đang build custom chips
- export restrictions
- supply catch-up
- hyperscaler CapEx có thể peak
- valuation quá cao

Counter-evidence không có nghĩa hypothesis sai.

Nó chỉ giúp ae tránh viết một câu chuyện quá sạch.

Thị trường ngoài đời hiếm khi sạch như vậy.

---

# 18. Correlation không phải causation

News xảy ra.

Stock giảm 5%.

Đừng tự động nói:

> Stock giảm vì news đó.

Cùng ngày có thể:

- Nasdaq giảm 4%
- cả sector bán tháo
- Fed vừa ra news
- competitor report earnings
- một fund lớn đang rebalance

Rất nhiều thứ xảy ra cùng lúc.

Project của bây đặc biệt dễ dính lỗi này vì evaluator sẽ nhìn outcome sau event.

---

# 19. Benchmark

Ví dụ NVIDIA giảm:

```text
-2%
```

Nghe bearish.

Nhưng semiconductor sector cùng ngày giảm:

```text
-6%
```

Thì NVIDIA actually outperform sector 4%.

Đó là lý do đôi lúc nhìn absolute price movement chưa đủ.

Một cách đơn giản:

```text
Excess Return
=
Stock Return - Benchmark Return
```

Ví dụ:

```text
NVDA: -2%
Sector: -6%

Excess Return = +4%
```

Benchmark có thể là:

- S&P 500
- Nasdaq
- sector ETF
- peers

Không có benchmark nào luôn đúng.

Chọn cái hợp lý với hypothesis.

---

# 20. Time horizon

Không phải mọi hypothesis đều đúng/sai vào ngày hôm sau.

Ví dụ:

> New factory sẽ tăng production capacity.

Mà ae evaluate bằng stock price ngày mai thì khá vô nghĩa.

Có hypothesis hợp với:

- 1 day
- 5 days
- 20 days

Có hypothesis phải đợi:

- next earnings
- next quarter
- 6 tháng
- 1 năm

Bây chỉ cần nhớ:

> **Outcome phải match với loại hypothesis đang test.**

---

# 21. Confidence

Nếu agent nói:

```text
confidence = 0.8
```

thì 0.8 không nên chỉ là con số trang trí.

Sau này nếu gom 100 prediction confidence khoảng 0.8 mà chỉ đúng 52 lần thì agent đang tự tin láo.

Nếu khoảng 80 lần đúng thì confidence khá calibrated.

Đó gọi là **calibration**.

## Brier Score

Biết cái này là đủ:

```text
Brier = (prediction probability - actual outcome)^2
```

Ví dụ agent nói:

```text
80% bullish
```

nhưng outcome bearish.

Penalty sẽ lớn hơn một prediction:

```text
55% bullish
```

mà sai.

Tức là:

> Sai mà còn tự tin vl thì bị phạt nặng hơn.

---

# 22. Hindsight bias

Đây là thứ project này phải chống từ đầu.

Nếu agent được nhìn outcome rồi mới giải thích:

> À stock giảm vì investors worried about margin.

thì dễ vl.

Nó có thể rationalize bất cứ thứ gì.

Phải làm kiểu:

```text
T0:
agent đọc information
↓
agent tạo hypothesis
↓
save lại
↓
không được sửa
↓
T+1 / T+5 / ...
outcome xuất hiện
↓
evaluate
```

Original hypothesis phải được time-lock.

Không thì feedback loop của ae chỉ đang học cách kể chuyện sau khi biết đáp án.

---

# 23. Mấy thứ chưa cần học

Ít nhất trong phase đầu, ae có thể bỏ qua:

- Options
- Futures
- Derivatives
- Black-Scholes
- Technical Analysis
- Chart Patterns
- CAPM
- Efficient Frontier
- Advanced Portfolio Theory
- Advanced Bond Math
- Advanced DCF
- Quant Factor Models
- High-frequency Trading
- Deep Market Microstructure

Sau này project đụng tới đâu thì học tiếp.

---

# 24. Một ví dụ full cho dễ hình dung

Giả sử một SaaS company vừa report earnings.

News:

```text
Revenue grew 25%.
```

Nghe ngon.

Nhìn kỹ hơn:

```text
Last quarter growth: 40%
Current growth: 25%
```

Growth vẫn cao, nhưng đang decelerate.

Tiếp:

```text
Gross margin:
80% → 72%
```

Margin giảm.

Management:

```text
Next quarter growth guidance: 18%
```

Market consensus trước đó:

```text
22%
```

Bây giờ story bắt đầu rõ hơn.

Có thể hypothesis là:

```text
Company growth is deteriorating faster than market expectations.
```

Evidence:

- revenue growth decelerating
- gross margin falling
- guidance below consensus

Counter-evidence:

- customer retention vẫn mạnh
- company vừa launch product mới
- weakness có thể chỉ temporary

Prediction:

```text
Bearish relative to SaaS peers over 1–5 days.
```

Confidence:

```text
0.72
```

Không có một framework thần thánh nào ở đây.

Chỉ là hiểu business rồi ráp những gì mình biết lại.

---

# 25. Học tới đâu là đủ?

Không cần học hết file rồi mới được build.

Khi bây mở một earnings report và không còn cảm giác:

> "đcm toàn số gì vậy"

mà bắt đầu đọc được story phía sau mấy con số, thì đủ để bắt đầu.

Trong lúc build gặp cái gì không hiểu thì học tiếp cái đó.

Finance rộng vãi.

Đừng có mục tiêu "học xong finance".

---

# Final Assignment

Chọn **một public company** mà ae thấy thú vị.

Có thể lấy:

- NVIDIA
- Tesla
- Meta
- Microsoft
- Spotify
- Netflix
- AMD
- Apple
- một company khác anh em hiểu business tương đối dễ

Đọc:

- earnings gần nhất
- management guidance
- vài news liên quan
- stock + sector movement

Sau đó viết lại bằng ngôn ngữ của mình.

Không cần theo format cứng.

Nhưng cuối cùng t muốn đọc xong và biết được:

- company kiếm tiền kiểu gì
- chuyện gì vừa thay đổi
- mấy con số nào đáng chú ý
- market trước đó đang mong đợi gì
- bây nghĩ chuyện gì đang xảy ra
- evidence support là gì
- evidence chống lại là gì
- hypothesis đó nên được check sau bao lâu
- nếu sai thì cái gì sẽ cho thấy nó sai

Nếu làm được cái đó thì đủ.

---

# Checklist cuối

## Business

- [ ] T giải thích được company kiếm tiền kiểu gì mà không cần đọc script.
- [ ] T biết business segment nào quan trọng.
- [ ] T biết vài thứ chính khiến revenue tăng/giảm.
- [ ] T biết vài cost quan trọng của company.

## Financials

- [ ] T hiểu Revenue là gì.
- [ ] T hiểu Gross Profit / Gross Margin đại khái nói lên điều gì.
- [ ] T hiểu Operating Income và Net Income khác revenue như nào.
- [ ] T biết EPS là gì.
- [ ] T hiểu profit và cash không phải cùng một thứ.
- [ ] T biết Operating Cash Flow, CapEx và FCF dùng để nhìn cái gì.

## Financial Statements

- [ ] Nhìn Income Statement t biết nó đang kể chuyện gì.
- [ ] Nhìn Balance Sheet t biết nó đang kể chuyện gì.
- [ ] Nhìn Cash Flow Statement t biết nó đang kể chuyện gì.

## Growth

- [ ] T hiểu YoY.
- [ ] T hiểu QoQ.
- [ ] T không chỉ nhìn growth rate mà còn hỏi growth đến từ đâu.
- [ ] T hiểu margin tăng/giảm có thể quan trọng như nào.

## Stocks

- [ ] T hiểu share là gì.
- [ ] T hiểu Market Cap.
- [ ] T hiểu IPO đại khái hoạt động ra sao.
- [ ] T hiểu secondary market.
- [ ] T biết bid, ask, order book và liquidity ở mức intuition.

## Valuation & Expectations

- [ ] T hiểu P/E đang nói đại khái cái gì.
- [ ] T hiểu P/S đang nói đại khái cái gì.
- [ ] T hiểu good company chưa chắc là good stock.
- [ ] T hiểu consensus estimate.
- [ ] T hiểu beat/miss.
- [ ] T hiểu guidance.
- [ ] T hiểu priced in.
- [ ] T hiểu market reaction phụ thuộc vào expectation chứ không chỉ good news/bad news.

## Reading Information

- [ ] T nhìn một event và biết nó có thể chạm vào phần nào của business.
- [ ] T có thể nối event với một vài financial metrics liên quan.
- [ ] T biết một event có thể có cả effect tốt và xấu.
- [ ] T biết tìm counter-evidence thay vì chỉ defend hypothesis của mình.

## Evaluation

- [ ] T hiểu correlation không đồng nghĩa causation.
- [ ] T biết tính return đơn giản.
- [ ] T hiểu tại sao cần benchmark.
- [ ] T hiểu excess return.
- [ ] T hiểu không phải hypothesis nào cũng check vào ngày hôm sau.
- [ ] T hiểu confidence là một probability claim có thể kiểm tra.
- [ ] T hiểu calibration ở mức cơ bản.
- [ ] T biết Brier Score đang punish cái gì.
- [ ] T hiểu tại sao hypothesis phải được time-lock trước khi nhìn outcome.

---

# Stop studying, start building

Nếu ae có thể lấy một earnings report thật và kể lại được kiểu:

> "Company này kiếm tiền như này. Quarter này cái này thay đổi. Market trước đó kỳ vọng cái kia. Data này làm t nghĩ X đang xảy ra. Nhưng có Y chống lại thesis đó. Nếu X đúng thì trong khoảng thời gian Z t kỳ vọng nhìn thấy chuyện này."

thì đủ.

Build đi.

Mấy thứ còn thiếu học sau.
