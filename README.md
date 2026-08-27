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

### How to run (Demo)

#### 1. Install dependencies

Use Python 3.10 or newer and create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

#### 2. Configure the OpenAI API key

Create a `.env` file in the project root. You can copy the example file:

```bash
cp .env.example .env
```

Then add your key:

```dotenv
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
```

The CLI loads this file automatically. An `OPENAI_API_KEY` and `TAVILY_API_KEY` should already be exported in your shell takes precedence over the value in `.env`.

#### 3. Run the application

From the project root, run:

```bash
python -m app.cli
```

To generate a different number of theses:

```bash
python -m app.cli --max-results 5
```

The application searches recent web sources, asks the language model to create
research theses, and prints the predictions, evidence, counter-evidence, and
confidence scores in the terminal.

The application needs internet access for web search and page fetching. It is
for learning and research only, not financial advice or automated trading.

