# Paper Proposal

## Working title

**Adaptive Agent or Fixed Pipeline? A Controlled Study of LLM Orchestration for Financial Event Forecasting**

## Proposal status

This is a proposal for a university paper. It defines planned research; it does not report completed implementation, experimental results, or trading performance.

## Abstract

Large language models can support financial research through either fixed multi-stage pipelines or autonomous agents that adaptively choose tools, revise intermediate beliefs, and decide when to stop. Existing work demonstrates agent architectures for reasoning and financial analysis, but it is often difficult to identify whether reported gains come from adaptive control, a stronger model, additional information, more tool calls, or a different evaluation harness. This study proposes a controlled comparison of three orchestration strategies: a single-shot LLM baseline, a fixed financial-research pipeline, and a bounded autonomous agent. All conditions use the same timestamped event inputs, base-model snapshot, output schema, feedback history, resource ceilings, and underlying data interfaces; the fixed pipeline and agent share the same callable tools. The systems forecast sector-adjusted returns for U.S. equities over 1-, 5-, and 20-trading-day horizons. They are evaluated along four primary dimensions: a deterministic matching score, probabilistic calibration, end-to-end latency, and monetary cost. A blinded LLM rubric with a four-person human audit provides secondary evidence about research quality. The primary experiment uses a frozen, time-gated historical corpus; a smaller live forward study tests external validity. The goal is not to build a trading strategy, but to isolate when adaptive agent control produces enough forecasting or reasoning value to justify its operational cost.

## 1. Motivation

An LLM pipeline and an LLM agent can use the same underlying model while behaving very differently.

- A fixed pipeline runs a predefined sequence of retrieval, analysis, and prediction stages.
- An agent observes intermediate results and chooses its next query, tool, revision, or stopping action.

The agent may investigate uncertainty more effectively, but it can also loop, drift, retrieve redundant evidence, consume more tokens, and take longer. A raw accuracy comparison is therefore insufficient. The experimental unit must include both forecast quality and the resources used to obtain it.

Finance makes the comparison especially demanding. Market outcomes are noisy; information availability changes over time; later articles can leak outcomes into historical research; and a plausible explanation is not necessarily a calibrated forecast. Event-study methodology provides a principled foundation for measuring market reactions around dated events, while probabilistic scoring distinguishes confidence from correctness.

## 2. Research gap

ReAct formalized interleaved reasoning and action, motivating agents that update plans from tool observations. Financial-agent systems such as FinMem and FinRobot demonstrate memory and multi-stage agent designs, but their goals and evaluation setups do not directly isolate adaptive orchestration from other system differences. ForecastBench emphasizes dynamic, contamination-resistant forecasting and proper probabilistic evaluation. Recent time-gated financial forecasting work further highlights calibration and look-ahead control.

The missing comparison for this project is narrower:

> When the base model, information, tools, schemas, history, and maximum resources are controlled, does adaptive agent control outperform a fixed pipeline for event-driven financial forecasts, and at what cost and latency?

This framing treats the execution harness as part of the experimental treatment rather than attributing every difference to the language model.

## 3. Research questions

### RQ1 — forecast matching

Under a locked experimental contract, does a bounded autonomous agent produce forecasts that better match realized sector-adjusted market reactions than a fixed pipeline?

### RQ2 — calibration

Does adaptive investigation improve the alignment between predicted class probabilities and observed outcomes?

### RQ3 — efficiency

What additional latency and monetary cost does the agent incur, and are any quality gains large enough to place it on the quality-efficiency Pareto frontier?

### RQ4 — research quality

Does the agent produce more causally coherent, evidence-grounded, expectation-aware analysis, even when deterministic forecast performance is similar?

### RQ5 — context dependence

Do differences vary by forecast horizon, event type, sector, evidence conflict, or retrieval depth?

## 4. Hypotheses

- `H1`: The agent achieves a higher mean deterministic matching score than the fixed pipeline.
- `H2`: The agent achieves a lower multiclass Brier score than the fixed pipeline.
- `H3`: The agent has higher latency and cost than the fixed pipeline.
- `H4`: The agent scores higher on blinded research-quality rubrics, especially counter-evidence handling and market-expectation awareness.
- `H5`: The fixed pipeline remains a competitive or preferable Pareto choice when agent gains are small relative to resource use.

The study does not assume the agent will win. A null result or a pipeline advantage would be practically meaningful for budget-constrained systems.

## 5. Contributions

The proposed paper aims to contribute:

1. a controlled, same-model comparison of single-shot, fixed-pipeline, and bounded-agent orchestration;
2. a shared time-gated schema for event evidence, forecasts, histories, and traces;
3. a four-dimensional evaluation of matching, calibration, latency, and cost;
4. a reproducible historical protocol plus a smaller live forward validation;
5. a condition-blind secondary rubric with human audit; and
6. a transparent account of failures, budget truncation, and leakage controls.

## 6. Experimental design

### Conditions

| Condition | Control policy | Adaptive tool use | Adaptive stopping |
|---|---|---:|---:|
| Single-shot | One fixed generation | No | No |
| Fixed pipeline | Registered stage graph | No | No |
| Bounded agent | Closed-loop plan/action controller | Yes | Yes |

The exact base-model snapshot, inference settings, input bundle, underlying data/tool implementations, output schema, maximum resource limits, and evaluator are shared.

The single-shot baseline receives context produced by preregistered non-adaptive retrieval over the same data interfaces; it cannot choose additional calls. The pipeline and agent share the same callable tools. Empirical-prior and always-`FLAT` forecasts are also reported as zero-cost statistical references, not experimental conditions.

### Forecast task

For a timestamped public-market event, each system forecasts a U.S. equity's sector-adjusted return over 1, 5, and 20 trading days. For every horizon, it outputs:

- probabilities for `DOWN`, `FLAT`, and `UP`;
- a selected direction and derived confidence;
- an expected excess return and registered 80% prediction interval; and
- evidence-linked reasoning.

The paper excludes fundamental-outcome forecasting in order to keep ground truth and scoring comparable across events.

### Data tracks

The primary historical track uses 200–500 stratified events and a frozen document corpus with strict information cutoffs. A development period supports implementation and rubric refinement; a later chronological test period remains sealed.

The secondary live track uses the same registered systems with real web retrieval. Forecasts are persisted before their outcomes resolve. This track tests external validity but is not allowed to replace the controlled historical result.

### History

Events are processed chronologically. Resolved feedback is released only after the corresponding horizon. For the primary comparison, every condition receives the same condition-blind pooled history snapshot at a given event. Arm-specific self-memory is reserved for a separately labeled ablation.

### Resource controls

All conditions receive the same ceilings for model tokens, tool calls, retrieved content, retries, and wall-clock time. They may consume less. Actual use is measured rather than artificially equalized.

The full operational protocol is specified in [experiment-protocol.md](experiment-protocol.md).

## 7. Evaluation

### 7.1 Deterministic matching

The headline matching score combines:

- 60% ordinal direction match; and
- 40% volatility-normalized magnitude accuracy.

The formula is frozen before test evaluation. Directional accuracy, macro-F1, Matthews correlation coefficient, MAE, RMSE, and both score components are reported alongside it. This prevents the composite score from hiding contradictory behavior.

### 7.2 Calibration

The primary calibration metric is multiclass Brier score. Negative log loss, classwise/top-label ECE, reliability plots, and forecast entropy provide supporting diagnostics. Calibration is evaluated from the full class distribution, not only a self-reported scalar confidence.

Expected-return 80% interval coverage and Winkler interval score are reported as additional uncertainty diagnostics.

### 7.3 Latency

End-to-end wall-clock latency includes model and tool time. The study reports median, p90, p95, timeout rate, and trace-level breakdowns.

### 7.4 Cost

Cost is computed from actual input/output tokens and metered tools using a versioned price snapshot. Raw token and call counts are also reported so the results remain interpretable if vendor prices change.

### 7.5 Secondary research quality

A blinded judge rates five dimensions using `UNSUPPORTED`, `WEAK`, `ADEQUATE`, and `STRONG`:

- causal coherence;
- evidence grounding;
- counter-evidence handling;
- market-expectation awareness; and
- specificity and resolvability.

Judge identity is configurable and reported. Output order is randomized, condition labels are removed, and repeated or ensembled judgments are used if the pilot budget allows. At least 50 outputs should be double-coded by members of the four-person team to estimate judge-human and human-human agreement.

## 8. Analysis plan

- Run three repetitions per event and condition.
- Use paired comparisons because conditions share event inputs.
- Cluster related tickers, horizons, and repetitions within the underlying event.
- Report event-clustered bootstrap confidence intervals, effect sizes, and a calendar-block bootstrap sensitivity analysis.
- Treat agent vs pipeline as the primary comparison.
- Use the single-shot baseline to measure whether orchestration itself adds value.
- Apply Holm correction to families of secondary tests.
- Report both failure-inclusive and valid-output-only analyses.
- Analyze the Pareto frontier rather than inventing one global score across quality, latency, and cost.

## 9. Budget and feasibility

Current resources include USD 20 in personal API budget and a possible VND 1–2 million in university support.

The study therefore begins with:

1. free synthetic validation of schemas, scorers, and leakage barriers;
2. a 20-event development pilot with three conditions and three repetitions, totaling 180 executions;
3. cost and variance estimation; and
4. a frozen main-study sample between 200 and 500 events, selected based on precision and confirmed funding.

At least 15% of confirmed funds is reserved for infrastructure failures, secondary judging, and the live track. If funding is insufficient, the study reduces stratified event count before changing models, conditions, schemas, or primary metrics. An underpowered study will be labeled a pilot rather than presented as decisive evidence.

## 10. Expected limitations

- Market reactions are noisy and do not prove that a generated causal explanation is true.
- Historical search corpora can contain subtle temporal leakage despite timestamp checks.
- The event sample may not represent all public equities or market regimes.
- Shared budget ceilings may favor one orchestration style.
- LLM judges can exhibit position, verbosity, and self-preference bias.
- A university-scale budget may detect only moderate or large effects.
- The live track may be small and incomplete at submission time, especially for the 20-day horizon.
- Results from one pinned base model do not establish universal agent-vs-pipeline behavior.

## 11. Ethical and interpretive boundaries

This work evaluates research-system behavior. It does not provide financial advice, execute trades, optimize a portfolio, or claim deployable profitability. Forecasts are evaluated as academic artifacts. The paper will disclose failed runs, data exclusions, model/tool versions, price assumptions, and source-licensing constraints.

## 12. Proposed paper structure

1. **Introduction** — motivation, narrow research gap, questions, and contributions.
2. **Related Work** — LLM agents, financial agents, forecasting benchmarks, event studies, and LLM judging.
3. **System Design** — shared contract and the three orchestration conditions.
4. **Dataset and Temporal Controls** — event construction, cutoff enforcement, histories, and outcome labels.
5. **Evaluation Methodology** — four primary dimensions, secondary rubric, and statistical plan.
6. **Results** — matching, calibration, latency, cost, failure rates, and Pareto analysis.
7. **Mechanism and Error Analysis** — tool trajectories, event categories, leakage audits, and qualitative cases.
8. **Limitations and Ethics** — validity boundaries and non-trading scope.
9. **Conclusion** — what the experiment supports, without generalizing beyond the tested model and harness.

Sections 6, 7, and 9 must remain unwritten as empirical claims until the registered experiment is complete.

## 13. Initial project plan

### Phase A — specification

- Freeze domain models and experiment schemas.
- Choose a pinned model and record inference parameters.
- Choose data providers and redistribution policy.
- Implement and unit-test the resolver/scorer first.
- Resolve the provider, date-range, intraday-baseline, budget-ceiling, and judge-model choices listed in the protocol without consulting sealed-test results.

### Phase B — condition implementation

- Implement single-shot, fixed-pipeline, and bounded-agent runners over shared interfaces.
- Add immutable traces, costs, timers, and cutoff enforcement.
- Verify that outcome data is inaccessible during prediction.

### Phase C — development pilot

- Construct 20 development events.
- Run 180 executions.
- Audit temporal leakage and system failures.
- Refine prompts/rubrics only on development data.
- Freeze main-study sample size and configuration.

### Phase D — main studies

- Run the sealed historical benchmark.
- Perform blinded automated judging and human audit.
- Begin the live forward evaluation early enough for 20-day resolution.
- Execute the preregistered statistical analysis.

### Phase E — writing and release

- Fill the Results section from generated tables and figures.
- Document deviations from the protocol.
- Release code, configurations, scoring logic, traces, and redistributable dataset artifacts.

## References

- Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review, 78*(1), 1–3. https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2
- Karger, E., Bastani, H., Chen, Y.-H., Jacobs, Z., Halawi, D., Zhang, F., & Tetlock, P. E. (2025). ForecastBench: A dynamic benchmark of AI forecasting capabilities. *International Conference on Learning Representations*. https://www.forecastbench.org/docs/
- MacKinlay, A. C. (1997). Event studies in economics and finance. *Journal of Economic Literature, 35*(1), 13–39. https://ideas.repec.org/a/aea/jeclit/v35y1997i1p13-39.html
- Shi, L., Ma, C., Liang, W., Ma, W., & Vosoughi, S. (2024). Judging the judges: A systematic study of position bias in LLM-as-a-judge. https://arxiv.org/abs/2406.07791
- Wataoka, K., Takahashi, T., & Ri, R. (2024). Self-preference bias in LLM-as-a-judge. https://arxiv.org/abs/2410.21819
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. *International Conference on Learning Representations*. https://openreview.net/forum?id=WE_vluYUL-X
- Yu, Y., Li, H., Chen, Z., Jiang, Y., Li, Y., Zhang, D., Liu, R., Suchow, J. W., & Khashanah, K. (2023). FinMem: A performance-enhanced LLM trading agent with layered memory and character design. https://arxiv.org/abs/2311.13743
- Zhou, T., Wang, P., Wu, Y., & Yang, H. (2024). FinRobot: AI agent for equity research and valuation with large language models. https://arxiv.org/abs/2411.08804

## Closely related work to address explicitly

A 2026 preprint, **FinBench: Time-Gated Calibration and Uncertainty Benchmarking for Agentic Financial Forecasting**, is unusually close to this proposal because it combines time gating, financial forecasts, Brier scoring, and interval evaluation. The final paper must verify its methods and position this study carefully: the proposed contribution here is the controlled orchestration comparison under a shared harness, with fixed-pipeline and single-shot baselines plus latency/cost analysis, rather than a claim to introduce time-gated financial calibration evaluation itself. See https://arxiv.org/abs/2607.16229.
