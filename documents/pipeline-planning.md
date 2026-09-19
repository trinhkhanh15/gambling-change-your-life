# MVP Architecture — Fixed Financial Research Pipeline

## Document status

This document is an implementation plan, not a description of currently verified system behavior. The existing repository is a demo and does not yet implement this architecture.

The fixed pipeline is one experimental treatment in a university study comparing three orchestration strategies:

1. a single-shot LLM baseline;
2. this fixed pipeline; and
3. a bounded autonomous agent.

The comparison is defined in [experiment-protocol.md](experiment-protocol.md). The agent counterpart is defined in [agent-planning.md](agent-planning.md).

## Objective

Build a reproducible financial-research workflow that converts a timestamped public-market event into testable forecasts, preserves the information available at prediction time, resolves forecasts against later market data, and exposes a feedback history.

The product loop is:

**Events → Thesis Analysis → Prediction → Reality → Evaluation → Feedback**

For the experiment, the pipeline's execution graph is fixed before the sealed test begins. An LLM may make semantic decisions inside a stage, but it may not decide which stage runs next, add steps, revisit an earlier stage, or decide its own stopping policy.

## Non-goals

- This is not a trading system and does not place or recommend trades.
- The MVP does not forecast revenue, earnings, margins, or other fundamental outcomes.
- The study does not claim profitability.
- The pipeline may maintain theses, but forecast evaluation is limited to sector-adjusted stock returns over fixed horizons.
- The MVP does not silently tune prompts, thresholds, budgets, or scoring after observing sealed-test results.

## Priority notation

- `P0`: required for the first valid experiment.
- `P1`: important after the P0 end-to-end loop works.
- `P2`: optional extension.

## Shared experimental contract

The single-shot baseline, pipeline, and agent must share the following contract. Differences outside the registered orchestration policy are experimental confounds. The same retrieval and data implementations back every condition; the single-shot condition receives the output of preregistered non-adaptive retrieval rather than choosing calls itself.

### Shared inputs

Each run receives an `EventBundle` containing:

- a stable `event_id`;
- the security and sector identifiers;
- the event timestamp and `information_cutoff`;
- source documents available by that cutoff;
- company and sector context available by that cutoff;
- a cutoff-safe `label_context` containing the sector benchmark, pre-event residual volatility, class thresholds, return convention, and interval level;
- an identical `history_snapshot_id`; and
- the forecast horizons `1D`, `5D`, and `20D`.

Historical runs use a frozen corpus. Live runs use the configured web-search service. Future prices and post-cutoff documents are inaccessible during prediction.

### Shared model and inference settings

- The exact base-model snapshot is configured once and recorded with every run.
- Model parameters, structured-output implementation, retry policy, and context limits are shared.
- Condition-specific instructions may describe the orchestration policy, but the financial role, definitions, output requirements, and scoring-relevant instructions remain shared.

### Shared tools

- `search_corpus(query, cutoff, limit)` for historical retrieval;
- `search_web(query, cutoff, limit)` for live retrieval;
- `fetch_document(document_id)`;
- `retrieve_company_context(ticker, cutoff)`;
- `retrieve_sector_context(sector_id, cutoff)`;
- `retrieve_history(snapshot_id, query, limit)`; and
- `calculate(expression)` for deterministic arithmetic.

Resolution prices and labels are served by a separate evaluator and are never available as prediction-time tools.

### Shared resource ceilings

Each condition has the same maximum:

- model input and output tokens;
- tool calls;
- document count and bytes returned;
- retries;
- wall-clock timeout; and
- accessible history records.

Actual usage may be lower and is logged for cost and latency evaluation.

### Shared forecast output

Every valid run must emit one forecast per requested horizon.

```json
{
  "event_id": "evt_001",
  "ticker": "XYZ",
  "information_cutoff": "2026-01-01T12:00:00Z",
  "thesis": "Concise causal claim",
  "evidence_ids": ["doc_1"],
  "counter_evidence_ids": ["doc_2"],
  "forecasts": [
    {
      "horizon": "1D",
      "direction": "UP",
      "probabilities": {"down": 0.15, "flat": 0.25, "up": 0.60},
      "confidence": 0.60,
      "expected_excess_return": 0.012,
      "expected_return_range": [-0.006, 0.030],
      "interval_level": 0.80,
      "reasoning": "Why this market reaction is expected"
    }
  ]
}
```

Validation rules include:

- probabilities are finite, in `[0, 1]`, and sum to one within tolerance;
- `direction` equals the probability argmax under the registered tie-break rule;
- `confidence` equals the maximum class probability;
- `interval_level` is exactly the registered `0.80`, and the interval endpoints are finite and ordered;
- all evidence references exist and were available by the cutoff;
- horizons are present exactly once; and
- return fields are numeric and use decimal units, where `0.01` means 1%.

Invalid output receives only the shared mechanical repair policy. No condition gets extra semantic retries.

## Fixed execution graph

```text
INGEST EVENT BUNDLE
        ↓
VALIDATE AND NORMALIZE
        ↓
RETRIEVE FIXED CONTEXT SET
        ↓
ROUTE THESIS: UPDATE | GENERATE | IGNORE
        ↓
MAINTAIN THESIS AND EVIDENCE
        ↓
GENERATE 1D / 5D / 20D FORECASTS
        ↓
DETERMINISTIC OUTPUT VALIDATION
        ↓
PERSIST FORECAST AND TRACE
        ↓
WAIT FOR HORIZON
        ↓
RESOLVE → SCORE → RELEASE FEEDBACK
```

The graph, retrieval limits, and number of model calls are registered before the test set is opened.

## 1. Event layer

### P0 — ingestion and temporal integrity

- Accept historical `EventBundle` records or live web events.
- Normalize source, title, timestamps, ticker, sector, event type, and document identifiers.
- Store both `published_at` and `retrieved_at`.
- Reject or quarantine documents whose availability by `information_cutoff` cannot be established.
- Preserve raw source material and content hashes for traceability where licensing permits.
- Classify event `nature` as `FACT`, `EXPECTATION`, or `MIXED`.
- Classify event `scope` as `COMPANY`, `INDUSTRY`, or `MACRO`.

### P0 — fixed retrieval

- Execute a preregistered set of retrieval calls and limits.
- Retrieve supporting context, contradictory context, market expectations, and shared history.
- Apply the same ranking and truncation policy to every condition.
- Store every query, result identifier, rank, timestamp, and cutoff decision.

### P1

- Cluster related documents into one event without losing individual provenance.
- Detect duplicates using deterministic identifiers plus similarity checks.

**Output:** a validated event and a fixed-size, cutoff-safe context package.

## 2. Thesis analysis layer

### P0 — thesis routing

Route the event to one of:

- `UPDATE_THESIS`: the event materially changes evidence for an existing core claim;
- `GENERATE_THESIS`: a new core claim is required;
- `IGNORE`: no testable market-reaction thesis is supported.

The route and rationale are stored. An event may affect multiple theses, but the number processed per run is capped identically across conditions.

`IGNORE` applies to thesis maintenance, not to the experimental forecast obligation. Every eligible benchmark event still receives a probability distribution for all three horizons; an uninformative event should be represented through probabilities near the registered prior rather than an unscored abstention.

### P0 — update thesis

- Append evidence and counter-evidence by immutable document ID.
- Update reasoning and strength.
- Keep, suspend, supersede, or kill the thesis with an explicit reason.
- Never change the core claim in place. A changed core claim creates a new thesis linked with `supersedes_thesis_id`.

### P0 — generate thesis

- Create a concise causal claim connecting the event to expected market reaction.
- Separate observed facts, inferred mechanisms, market expectations, and uncertainties.
- Avoid duplicates against the shared thesis registry.

### Thesis semantics

- `strength` measures evidential support for the thesis.
- Forecast probability measures uncertainty about a future return class.
- A weak forecast does not automatically kill a thesis.
- A failed forecast does not by itself invalidate the causal thesis.

**Output:** versioned thesis records and a cutoff-safe evidence package.

## 3. Prediction layer

### P0 — forecast generation

For each of `1D`, `5D`, and `20D`, generate:

- probabilities for `DOWN`, `FLAT`, and `UP`;
- the selected direction and derived confidence;
- expected sector-adjusted return;
- an expected-return interval;
- the registered 80% interval level;
- evidence-grounded reasoning; and
- an explicit information cutoff.

The model must consider:

- fundamentals relevant to the event;
- what the market plausibly expected before the event;
- whether information may already be priced in;
- supporting and contradictory evidence; and
- horizon-specific causal timing.

The workflow may ask a fixed number of predefined questions about expectations. It cannot recursively invent additional analysis steps.

### P0 — prediction versioning

- Forecast records are immutable.
- Materially changed forecasts create a new version linked by `supersedes_forecast_id`.
- Superseded forecasts remain resolvable and scorable from their original cutoff.
- Analysis may supersede a forecast but may never mark it correct or incorrect.

**Output:** schema-valid forecasts and an immutable execution trace.

## 4. Resolution and feedback layer

This layer is deterministic and shared by all experimental conditions.

### P0 — resolution

- Open a forecast only after its horizon is reached and required market data is available.
- Compute the registered sector-adjusted return from the registered baseline.
- Map the realized normalized return to `DOWN`, `FLAT`, or `UP`.
- Mark missing, halted, delisted, corporate-action-affected, or otherwise invalid cases according to preregistered exclusion rules.
- Never overwrite the original forecast or information cutoff.

### P0 — evaluation

- Calculate the deterministic matching score.
- Calculate multiclass Brier score, negative log loss, ECE, and directional/magnitude diagnostics.
- Record end-to-end latency, model latency, tool latency, tokens, tool usage, retries, and estimated USD cost.
- Run blinded rubric judging as a separate secondary evaluation.

### P0 — feedback

- Release feedback only after the relevant horizon resolves.
- Add resolved cases to the shared chronological history under the protocol's pooling policy.
- Preserve the prediction, actual outcome, score components, and failure classification.
- Make the identical snapshot available to all conditions for the same subsequent event.

### P1

- Retrieve similar resolved failure cases during future analysis.
- Classify recurring failures as evidence retrieval, causal reasoning, expectation modeling, direction, magnitude, or calibration errors.

## 5. Observability and reproducibility

### P0 trace fields

- experiment, dataset, event, condition, repetition, and run identifiers;
- model snapshot and inference parameters;
- prompt-template hashes;
- tool schema and implementation versions;
- input snapshot and history snapshot identifiers;
- every model and tool call with monotonic timestamps;
- token counts, retries, errors, and cost inputs;
- raw output, validated output, and repair attempts; and
- code commit and environment metadata.

Condition identifiers must be removed from artifacts passed to LLM or human judges.

## 6. Failure policy

Failures are results, not invisible cleanup work.

- `INVALID_INPUT`: event bundle violates the contract.
- `CUTOFF_VIOLATION`: retrieved material is unavailable at prediction time.
- `TOOL_FAILURE`: a tool fails after the shared retry limit.
- `INVALID_OUTPUT`: forecast remains schema-invalid after mechanical repair.
- `TIMEOUT`: wall-clock budget is exceeded.
- `BUDGET_EXCEEDED`: tool or token ceiling is exceeded.
- `UNRESOLVABLE`: outcome data cannot validly resolve the forecast.

Report failure rates by condition. Do not discard condition failures from accuracy, latency, or cost analysis without showing both intention-to-evaluate and valid-output analyses.

## 7. MVP delivery order

1. Freeze shared schemas, cutoff rules, trace format, and condition budgets.
2. Build historical event-bundle validation and frozen-corpus retrieval.
3. Implement the deterministic resolver and scorer before optimizing prompts.
4. Implement the single-shot baseline.
5. Implement this fixed pipeline exactly as registered.
6. Implement the bounded agent using the same interfaces.
7. Run a development-only smoke test and cutoff audit.
8. Run the budget pilot and finalize feasible sample size without inspecting sealed-test arm differences.
9. Freeze prompts, hashes, config, and test set.
10. Run the historical main study, followed by the live forward study.

## Minimum success criterion

The MVP succeeds when all three conditions can consume the same cutoff-safe event and history snapshot, produce the same output schema under the same resource ceilings, be resolved by the same deterministic evaluator, and generate complete traces for matching, calibration, latency, cost, and secondary research-quality analysis.
