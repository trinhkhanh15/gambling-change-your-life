```json
{
  "event": {
    "id": "evt_001",
    "published_at": "2025-02-12T08:30:00Z",
    "source": "Reuters",
    "title": "Company X cuts full-year guidance after weak China demand",
    "content": "...",
    "companies_mentioned": ["Company X"],
    "sectors": ["Consumer Discretionary"]
  },

  "company": {
    "ticker": "XYZ",
    "business_segments": [
      {"name": "North America", "revenue_pct": 42},
      {"name": "Europe", "revenue_pct": 25},
      {"name": "China", "revenue_pct": 18}
    ],
    "recent_financials": {
      "revenue_growth_yoy": 4.2,
      "gross_margin": 43.1,
      "operating_margin": 11.4
    }
  },

  "market_context": {
    "price_before_event": 82.4,
    "market_cap": 41000000000,
    "sector_return_5d": -1.2,
    "sp500_return_5d": 0.4
  }
}
```

## Data model questions
1. Thông tin nào là input bắt buộc để agent phân tích được một event?
2. News nói về một company nhưng tác động có thể sang company khác thì represent relationship kiểu gì?
3. Một hypothesis cần lưu những gì để sau này evaluate được? 
4. Nếu cùng một event có 3 hypothesis khác nhau thì data model xử lý thế nào?
5. Stage nào deterministic, stage nào cần LLM?

## Pipeline design questions
1. Input của system là gì?
2. Output cuối cùng muốn system trả ra cái gì?
3. Để biến input thành output đó, system cần làm những việc gì?
4. Những việc đó nên chạy theo thứ tự nào?
5. Mỗi bước nhận cái gì và trả ra cái gì?


## Open questions

1. khi 1 event tới, ai quyết định update thesis cũ / tạo thesis mới / không liên quan?
2. làm sao để biết 1 event có khả năng liên quan, embedding/top-k hay vứt hết vào LLM?
3. 1 event có update được nhiều thesis không? 
4. update thesis là update cái gì? confidence, reasoning, evidence, hoặc hypothesis?
5. ngưỡng nào khiến thesis dead
6. làm sao chắc chắn 1 thesis k bị update thành 1 thesis hoàn toàn mới
7. có nên lưu version cho thesis không, nếu có thì lưu những gì, như nào?
8. Game theory xuất hiện ở layer nào? Nếu agent nghĩ “market nghĩ rằng market sẽ nghĩ...” thì dừng recursion ở đâu
9. Làm sao phân biệt good business news với positive surprise relative to expectation?





