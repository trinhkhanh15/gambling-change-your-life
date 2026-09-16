# Experimental Protocol — Agent vs Fixed Pipeline for Financial Event Research

## Status and purpose

This document is the preregistration-oriented protocol for a planned university study. It defines the comparison before data collection and is not evidence that the system has been implemented or evaluated.

The protocol compares orchestration strategies, not model families. Its central rule is:

> Hold the task, information, base model, tools, schemas, resource ceilings, history, and evaluator constant; vary the control policy.

## 1. Research conditions

### C0 — single-shot baseline

One model call receives the shared event bundle plus a fixed context package and emits the common forecast schema. It cannot call tools adaptively.

### C1 — fixed pipeline

A preregistered graph performs fixed retrieval, thesis analysis, prediction, and validation stages. The number and order of stages are fixed. See [pipeline-planning.md](pipeline-planning.md).

### C2 — bounded agent

A closed-loop controller chooses queries, tools, revisiting, and stopping within the shared ceilings. See [agent-planning.md](agent-planning.md).

### Non-LLM reference forecasts

Two zero-cost references contextualize whether any LLM condition has forecast skill:

- the empirical class distribution estimated only from the development set; and
- an always-`FLAT` forecast with a preregistered probability distribution.

These are scoring references, not additional orchestration treatments.

## 2. Evaluation tracks

### Track A — controlled historical benchmark

This is the primary study.

- Use frozen event bundles and a frozen cutoff-safe document corpus.
- Process events in chronological order.
- Resolve predictions against later market data unavailable to the systems.
- Use a development set for engineering and threshold validation.
- Keep a temporally later test set sealed until the harness, prompts, metrics, budgets, and exclusions are frozen.

### Track B — live forward evaluation

This is a secondary external-validity study.

- Use the same conditions and schemas with the live web-search tool.
- Record the real retrieval and prediction timestamps.
- Publish or hash forecasts before outcomes resolve.
- Apply thresholds and scoring fixed by Track A.
- Report unresolved forecasts rather than dropping them.

Track B may be smaller because its 20-day horizon requires calendar time and live API spending.

## 3. Task definition

Given a market event and information available by its cutoff, predict the security's sector-adjusted return over `1D`, `5D`, and `20D` trading-day horizons.

### Scope

- U.S.-listed liquid large- and mid-cap equities.
- Event classes: earnings, guidance, regulation, M&A, product, and supply-chain events.
- Initial target: 200–500 historical event bundles, subject to the registered budget-pilot rule.
- Stratify sampling by event type, sector, horizon availability, and calendar period.
- Prevent the same underlying event or near-duplicate documents from crossing development and test splits.

### Exclusions

Register deterministic exclusions before opening the test set, including:

- ambiguous or unverifiable publication time;
- missing baseline or horizon prices;
- trading halt spanning the required baseline;
- delisting or ticker mapping that cannot be reconstructed;
- unadjusted split or other unresolved corporate action;
- event duplication; and
- evidence that the frozen corpus contains post-cutoff outcome information.

Show the full exclusion flow by condition and reason.

## 4. Event-time and outcome construction

The study measures market reaction, not implementable post-inference trading returns.

### Baseline price

- Before regular market open: previous regular-session close.
- During regular market hours: last completed eligible fixed interval ending at or before the event timestamp; the interval length is selected before dataset construction and applied uniformly.
- After regular market close: that session's close.
- If timestamp precision is insufficient to select the registered baseline, exclude the event.

The historical MVP should prioritize events outside regular hours because they can be resolved with lower-cost daily data and less ambiguous timestamps. In-session events may be included only when reliable intraday timestamps and prices are available.

### Realized excess return

The endpoint for horizon `h` is the `h`-th eligible regular-session close after the event becomes public, counting the current session as day 1 for a pre-open or in-session event and the next session as day 1 for an after-close event.

For security `i`, sector benchmark `s`, and horizon `h`, use adjusted prices and log returns:

```text
r_i,h = log(P_i,h / P_i,0)
r_s,h = log(P_s,h / P_s,0)
excess_return_i,h = r_i,h - r_s,h
```

The primary benchmark is the preregistered liquid sector ETF. An index-adjusted sensitivity analysis may be reported separately.

### Volatility normalization and realized class

Estimate pre-event daily residual volatility from a fixed estimation window that ends before the event, initially proposed as trading days `[-120, -21]`. Define:

```text
normalized_return_i,h = excess_return_i,h / (residual_volatility_i * sqrt(h))
```

Initial registered class thresholds:

- `DOWN` when normalized return `< -0.5`;
- `FLAT` when normalized return is in `[-0.5, 0.5]`;
- `UP` when normalized return `> 0.5`.

Development data may be used once to verify that these thresholds do not create unusably sparse classes. Any change must be frozen and justified before the sealed test, never selected to improve an arm's test result.

Magnitude bands for diagnostics are:

- `SMALL`: absolute normalized return in `[0.5, 1.0)`;
- `MEDIUM`: `[1.0, 2.0)`;
- `LARGE`: `>= 2.0`.

## 5. Shared forecast schema

Each execution emits one forecast object containing three horizon forecasts.

Required horizon fields:

```text
horizon: 1D | 5D | 20D
probabilities: {down, flat, up}, summing to 1
direction: argmax(probabilities)
confidence: max(probabilities)
expected_excess_return: decimal return
expected_return_range: [low, high]
interval_level: 0.80
reasoning: evidence-grounded text
```

Required record fields include event, ticker, cutoff, thesis, evidence IDs, counter-evidence IDs, schema version, and trace ID. The shared input includes cutoff-safe label context: sector benchmark, pre-event residual volatility, class thresholds, return convention, and the 80% interval level. This lets every condition interpret the output classes identically without exposing future outcomes.

The deterministic tie-break order for equal maximum probabilities is `FLAT`, then `DOWN`, then `UP`. Schema checks are deterministic.

There is no abstention in the primary benchmark. A system that finds the event uninformative must still issue a distribution, normally close to the registered prior, and explain its uncertainty. This prevents selective forecasting from inflating performance.

## 6. Information and history controls

### Frozen historical corpus

- Store document IDs, content hashes, source URLs, publication timestamps, retrieval timestamps, and cutoff eligibility.
- Search and fetch operate only over this corpus.
- The prediction environment has no route to market outcomes or the open web.
- Run automated date scans and manual cutoff audits on a sample.

### Live web

- Use one configured search provider and versioned wrapper for all conditions.
- Apply identical result limits and cutoff filtering.
- Archive eligible search metadata and hashes where licensing allows.
- Flag uncertain availability rather than assuming a page existed at the cutoff.

### Shared chronological history

- A resolved item is unavailable until its horizon has elapsed.
- At event `t`, all conditions receive the exact same `history_snapshot_id`.
- The primary ledger pools condition-blinded earlier forecasts, observed outcomes, score components, and failure lessons, then exposes the same ordered records to all conditions.
- Retrieval ceilings are shared; the agent chooses its history queries while the pipeline uses fixed queries.
- Arm-specific self-memory is a separate exploratory ablation because its content differs across conditions.

The pooled-history policy means the primary experiment tests adaptive use of a common feedback resource, not private self-improvement.

## 7. Fairness and locked harness

Record and freeze:

- exact base-model snapshot and inference parameters;
- financial task instructions and schema descriptions;
- condition controller prompts;
- tool names, schemas, implementations, result caps, and retry behavior;
- maximum tokens, calls, documents, bytes, and wall-clock time;
- history snapshot construction;
- output repair policy;
- package lockfile, code commit, and environment; and
- prompt and configuration hashes.

The maximum budget is equal across conditions. Actual usage is allowed to differ and is an outcome. A single-shot run does not receive extra context merely because it cannot adaptively search; it receives the same registered initial package.

## 8. Primary evaluation dimensions

The study has four headline dimensions. No single overall ranking combines all four.

### 8.1 Matching score — higher is better

Map classes to `DOWN=-1`, `FLAT=0`, and `UP=1`.

```text
direction_score = 1 - abs(predicted_class - actual_class) / 2

predicted_normalized_return =
    expected_excess_return / (residual_volatility * sqrt(h))

magnitude_score =
    max(0, 1 - abs(predicted_normalized_return - actual_normalized_return) / 2)

matching_score = 0.6 * direction_score + 0.4 * magnitude_score
```

The weights and divisor are frozen before test evaluation. Report the composite together with:

- directional accuracy;
- macro-F1 and Matthews correlation coefficient;
- excess-return MAE and RMSE;
- direction and magnitude components; and
- performance by horizon, event type, and sector.

The formula is a study-specific utility score, not a proper scoring rule. Conclusions must remain robust when the components are shown separately.

### 8.2 Calibration — lower is better

Primary calibration metric:

```text
multiclass_brier = sum_k (p_k - y_k)^2
```

Also report:

- negative log loss with a preregistered numerical floor;
- classwise and top-label expected calibration error;
- reliability diagrams;
- sharpness or entropy;
- empirical coverage and Winkler interval score for the expected-return interval; and
- calibration slope/intercept when sample size permits.

ECE depends on binning and is not used alone. The protocol and code must freeze adaptive or fixed bin definitions before test analysis.

### 8.3 Latency — lower is better

Measure monotonic wall-clock time from condition invocation to final validated output.

Report:

- median, p90, and p95 end-to-end latency;
- model and tool time when separable;
- timeout rate; and
- agent step count and pipeline stage count.

Historical runs should avoid uncontrolled parallelism that gives one condition a concurrency advantage. Track B additionally reports network/provider variance.

### 8.4 Cost — lower is better

Calculate actual per-run cost from:

- input, cached-input, and output tokens by model-call type;
- search, fetch, and other metered tool calls; and
- the price table snapshot recorded on the run date.

Report mean, median, p90, total USD, and cost per valid forecast. Also report token and call counts so results remain interpretable after vendor prices change.

## 9. Secondary research-quality evaluation

This score is not part of deterministic market matching.

### Rubric dimensions

Each dimension receives one enum:

```text
UNSUPPORTED = 0
WEAK = 1
ADEQUATE = 2
STRONG = 3
```

Dimensions:

1. `causal_coherence` — the causal path from event to market reaction is explicit and plausible;
2. `evidence_grounding` — claims are supported by eligible evidence IDs;
3. `counter_evidence_handling` — relevant contrary information is represented fairly;
4. `expectation_awareness` — the analysis distinguishes the event from what may already be priced in;
5. `specificity_and_resolvability` — the reasoning supports the exact ticker, direction, and horizon rather than vague commentary.

Report each dimension and their unweighted mean. Do not merge this mean into `matching_score`.

### Judge protocol

- Strip condition labels and system-specific metadata.
- Randomize presentation order.
- Configure judge model(s) separately from generator conditions.
- Prefer independent judge families; if the same family is used, disclose possible self-preference bias.
- Run repeated judgments or a small ensemble if the budget pilot supports it.
- Give judges the same rubric, event context, and evidence package.
- Preserve raw judge outputs and failures.

### Human audit

The four-person team should independently double-code at least 50 outputs if feasible, stratified across conditions and score levels. Before adjudication, report:

- human-human agreement using weighted kappa or Krippendorff's alpha as appropriate;
- judge-human agreement per dimension; and
- confusion matrices, not only correlation.

Audit assignments remain blinded to condition. Resolve rubric ambiguity on development examples before sealed-test judging.

## 10. Repetitions and statistical analysis

- Run three independent repetitions per event and condition with registered randomness settings.
- Keep event, input snapshot, history snapshot, and resource ceilings paired across conditions.
- Treat the underlying event cluster as the primary resampling unit; related tickers, horizons, and repetitions remain together.
- Report paired mean or median differences with event-clustered bootstrap 95% confidence intervals and a calendar-block bootstrap sensitivity analysis for sequential dependence.
- Report effect sizes, not only p-values.
- Correct families of secondary hypothesis tests using Holm's method.
- Show failure-inclusive and valid-output-only analyses.
- Do not choose a favorable repetition after inspection.

The main comparison is C2 vs C1. C0 contextualizes whether orchestration adds value.

## 11. Budget-aware sample plan

Available funding is currently approximately:

- personal API budget: USD 20;
- possible university support: VND 1–2 million;
- total exact budget: to be recorded when funding is confirmed.

### Phase 0 — non-API validation

Test schemas, cutoff enforcement, scoring, trace completeness, and synthetic failures without paid calls.

### Phase 1 — budget pilot

- Use 20 development events.
- Run `20 events × 3 conditions × 3 repetitions = 180 executions`.
- One execution should produce all three horizons.
- Include judge cost on a small stratified subset.
- Estimate per-condition cost, variance, failure rate, and latency.

### Phase 2 — freeze feasible main sample

Use pilot cost and variance, not observed condition superiority, to choose the historical sample between 200 and 500 events. Reserve at least 15% of confirmed funds for retries caused by infrastructure failures, judging, and the live track.

If the full design exceeds funding:

1. preserve all three conditions;
2. preserve three repetitions for the primary historical comparison if possible;
3. reduce event count using stratified sampling;
4. reduce judge ensemble size before weakening deterministic forecast evaluation; and
5. label the work a pilot study if precision remains inadequate.

Do not silently substitute a cheaper model after starting the sealed test.

## 12. Hypotheses

- `H1`: The bounded agent has a higher mean matching score than the fixed pipeline under equal resource ceilings.
- `H2`: The bounded agent has a lower multiclass Brier score than the fixed pipeline.
- `H3`: The bounded agent has higher end-to-end latency and cost than the fixed pipeline.
- `H4`: The agent receives higher secondary research-quality ratings, especially for counter-evidence and expectation awareness.
- `H5`: The fixed pipeline may remain preferable on the Pareto frontier when matching/calibration gains are small relative to cost and latency.

H1–H4 are directional hypotheses. H5 is a decision analysis rather than a null-hypothesis test.

## 13. Pareto and robustness analysis

Do not collapse matching, calibration, latency, and cost into one arbitrary master score.

- Plot matching vs cost and matching vs latency.
- Identify dominated and non-dominated conditions.
- Repeat conclusions by horizon and event type.
- Run matching-score sensitivity at alternative direction/magnitude weights, clearly labeled secondary.
- Compare sector-adjusted and index-adjusted outcomes.
- Report with and without unresolvable cases under the registered policy.

## 14. Threats to validity

- **Temporal leakage:** cached or retrieved documents may reveal later outcomes.
- **Event selection bias:** handpicked salient events can exaggerate predictability.
- **Dependence:** several tickers or articles may represent the same underlying event.
- **Non-stationarity:** historical performance may not transfer to the live period.
- **Harness confounding:** condition prompts or retry behavior may differ beyond control flow.
- **Budget truncation:** the agent may be disproportionately harmed or helped by the chosen ceiling.
- **Judge bias:** position, verbosity, and self-preference can distort secondary scores.
- **Composite-score sensitivity:** matching weights encode a study-specific value judgment.
- **Market-reaction interpretation:** abnormal return does not prove that the system's causal explanation is correct.
- **Power:** a budget-constrained university study may only estimate large effects reliably.

## 15. Ethics and reporting boundaries

- The system is for research and education, not financial advice.
- Do not report simulated returns as deployable trading performance.
- Respect source licenses; store hashes and metadata when full redistribution is prohibited.
- Document API providers, model versions, prices, exclusions, and all failed runs.
- Publish code, configurations, schemas, scoring logic, and redistributable dataset artifacts when possible.

## 16. Freeze checklist

Before the first sealed-test call, archive:

- [ ] research questions and hypotheses;
- [ ] dataset manifest and temporal split;
- [ ] event-time, baseline, benchmark, and exclusion rules;
- [ ] schema and validator version;
- [ ] matching and calibration implementations;
- [ ] judge rubric and human-audit instructions;
- [ ] exact model and tool versions;
- [ ] prompts and configuration hashes;
- [ ] resource ceilings and retry policy;
- [ ] history pooling and release policy;
- [ ] repetition and randomization settings;
- [ ] statistical-analysis code; and
- [ ] confirmed monetary budget and reserve.

## 17. Decisions intentionally left for the development phase

These choices are not yet evidence and must be resolved before the freeze checklist is signed:

- exact pinned base-model identifier and inference parameters;
- historical document, intraday price, daily price, and sector-classification providers;
- historical date range and final temporal split;
- exact intraday interval for eligible in-session events;
- final per-condition token, tool, document, retry, and time ceilings;
- calibration-bin construction and numerical log-loss floor;
- whether one or multiple judge models fit the pilot budget;
- confirmed funding and resulting main-study event count; and
- live-track start date and achievable resolved sample before the university deadline.

These decisions may use development data, feasibility checks, and pilot cost estimates. They may not use sealed-test arm results.
