## Gambling change your life

### What is it?

Basic project about how to build AI agent for consume news, report,.. for generating market hypothesis. Then validate it by next merket data and improve the agent. 

### Need to know

Not for trading, fucking not. This project only for improve technical ability and know how the market going. 

### What you can do after this project

**Technical**:

- Know how to build AI agent, basic feedback loop. 

**Business/Finance**:

- Know how something affect to business.
- Know what happend in stock market.

**Example outcome**:

```markdown
Company: NVIDIA

What happended:
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

## Runnable integration slice

The current implementation connects the shared contracts and adapters through
`Event -> Thesis -> Prediction -> Reality -> Evaluation`. Run the deterministic
demo with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m app.demo
python -m pytest -q
```

The demo uses a mock LLM, a fixture source, and JSON persistence under
`data_storage/`. It creates a synthetic reality record after the prediction
horizon; it verifies plumbing and scoring contracts, not forecasting quality.

`OpenAIAdapter` and `TavilySourceAdapter` implement the same ports used by the
mock pipeline. They require `OPENAI_API_KEY` and `TAVILY_API_KEY` respectively
when selected by a caller.
