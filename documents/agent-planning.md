# MVP Architecture — Bounded Financial Research Agent

## Document status

This is an implementation plan for the agent treatment in the proposed university study. It is not implemented or experimentally validated by the current demo.

The shared data, schemas, tools, budgets, resolution rules, and evaluation protocol are defined in [experiment-protocol.md](experiment-protocol.md). The fixed comparison condition is defined in [pipeline-planning.md](pipeline-planning.md).

## Objective

Build a bounded autonomous agent that can decide how to investigate a timestamped market event before producing the same testable forecast schema as the fixed pipeline.

The agent may decide:

- which permitted tool to call;
- how to formulate retrieval queries;
- which evidence gaps deserve another step;
- whether to revisit or revise its current thesis;
- whether contradictory evidence is sufficient;
- and when to stop before reaching the shared resource ceilings.

The agent may not change the task, schemas, cutoff, accessible data, evaluator, or resource ceilings.

## Experimental definition of an agent

For this study, an agent is not merely an LLM called in a loop. It is a closed-loop controller with state, observations, permitted actions, and a stopping decision:

```text
state_t + observation_t
          ↓
        PLAN
          ↓
 choose ACTION or FINALIZE
          ↓
 tool observation / validated forecast
          ↓
 update state_(t+1)
```

The distinguishing treatment is adaptive control flow. The base model, financial instructions, prediction schema, tools, history snapshot, and maximum resources remain locked with the other conditions.

## Non-goals

- No multi-agent society is required for the MVP.
- No autonomous trading, portfolio allocation, or order execution.
- No access to future prices, resolution labels, or post-cutoff documents.
- No hidden prompt optimization during the sealed test.
- No unrestricted recursive self-reflection.
- No claim that longer reasoning is inherently better.

## Shared contract

The agent consumes the same `EventBundle` and emits the same forecast object described in [pipeline-planning.md](pipeline-planning.md). It receives:

- the same pinned base-model snapshot and inference settings;
- the same versioned tool implementations;
- the same `history_snapshot_id` for an event;
- the same document, token, tool-call, retry, and wall-clock ceilings; and
- the same deterministic output validator and mechanical repair policy.

The agent can use less than the ceiling. Actual usage is a measured outcome.

## Agent state

### P0 — immutable task state

- `run_id`, `event_id`, `ticker`, and condition-blind event metadata;
- `information_cutoff` and eligible horizon definitions;
- shared budget ceilings and current usage;
- tool schemas and cutoff policy; and
- output-schema version.

### P0 — working state

- current event interpretation;
- candidate theses and their status;
- known facts and linked evidence IDs;
- assumptions and unsupported claims;
- counter-evidence;
- unresolved questions;
- current market-expectation model;
- draft horizon forecasts;
- retrieved history cases; and
- an append-only action/observation trajectory.

Working state is not long-term memory. Long-term information enters only through the shared history tool.

## Allowed actions

```text
SEARCH(query, source_scope)
FETCH(document_id)
GET_COMPANY_CONTEXT(ticker)
GET_SECTOR_CONTEXT(sector_id)
GET_HISTORY(query)
CALCULATE(expression)
UPDATE_WORKING_THESIS(...)
FINALIZE(forecast_output)
```

`UPDATE_WORKING_THESIS` is internal structured state mutation, not an external tool. Every external action and observation is logged.

No generic code execution, shell, unrestricted browsing, or evaluator endpoint is exposed in the primary experiment.

## Control loop

### 1. Observe

Read the event bundle, cutoff, requested horizons, available context, and remaining budget. Separate sourced facts from interpretations.

### 2. Plan

Produce a short structured next-step decision:

```json
{
  "state_summary": "What is currently known",
  "uncertainty": "Most decision-relevant unresolved issue",
  "action": "SEARCH",
  "action_input": {"query": "..."},
  "expected_value": "How this could change a forecast",
  "stop_after_observation_if": "Explicit criterion"
}
```

The plan is bounded to the next action. The agent does not generate a long unverifiable plan that consumes the budget without interacting with evidence.

### 3. Act

Execute one permitted action. The harness enforces input validation, cutoff restrictions, output-size limits, timeouts, and budget accounting.

### 4. Reflect

Update structured working state based on the observation:

- Did the observation add a new fact?
- Does it support or contradict a candidate thesis?
- Does it change expected direction, magnitude, or uncertainty?
- Is the source eligible and independent of existing evidence?
- What important uncertainty remains?

Reflection is part of the next controller call rather than an unlimited separate model call unless the registered configuration explicitly allocates one.

### 5. Stop or continue

The agent finalizes when any of the following holds:

- the expected value of another tool call is low;
- evidence and counter-evidence are sufficient to express calibrated uncertainty;
- the remaining uncertainty is not resolvable with available tools;
- the next call would violate a ceiling; or
- the harness forces finalization at the registered step or time limit.

The agent must not use confidence as a reason to hide missing evidence. Low confidence is a valid outcome.

## Thesis and forecast behavior

### P0 — thesis routing

The agent may explore several candidate theses, then emit `UPDATE_THESIS`, `GENERATE_THESIS`, or `IGNORE` decisions under the shared thesis rules.

- A core claim is immutable after persistence.
- A materially changed claim becomes a linked new thesis.
- Evidence, counter-evidence, reasoning, strength, and lifecycle status are versioned.
- Thesis strength and forecast confidence remain distinct.

### P0 — horizon forecasts

The agent must finalize all requested horizons in one schema-valid output. Each horizon includes:

- a full `DOWN`/`FLAT`/`UP` probability distribution;
- direction and derived confidence;
- expected sector-adjusted return and interval;
- the registered 80% interval level;
- horizon-specific reasoning; and
- shared evidence references.

The agent may reach different causal conclusions by horizon but may not issue ambiguous or non-resolvable predictions.

## History and feedback

### Primary study

- History is time-gated and released only after resolution.
- All conditions receive the exact same snapshot for the same event.
- The shared ledger contains cutoff-safe resolved cases, observed outcomes, score components, and condition-blinded failure lessons under the pooling rule in the protocol.
- The agent decides whether and how to retrieve from that snapshot; the pipeline uses its registered fixed history retrieval.

### P1 exploratory ablation

An arm-specific self-memory study may allow each condition to retrieve only its own earlier forecasts and errors. It must be reported as a separate experiment because the inputs are no longer identical across conditions.

## Budget enforcement

### P0

The harness checks before each action:

- model-token budget remaining;
- tool-call budget remaining;
- returned-document budget remaining;
- wall-clock time remaining; and
- retry allowance remaining.

When the next action cannot fit, the harness requests `FINALIZE` with the current evidence. If no valid output is produced, the run is recorded as `BUDGET_EXCEEDED`, `TIMEOUT`, or `INVALID_OUTPUT`; it is not silently rerun with extra resources.

## Safety and leakage controls

- Every retrieval request includes the immutable cutoff.
- Search results require a verified availability timestamp.
- Documents without adequate timestamp provenance are quarantined.
- Resolution tools and post-event price outcomes are isolated in a separate process or permission boundary.
- Tool responses are treated as untrusted data, not instructions.
- Prompts and retrieved pages cannot grant new tools or alter budgets.
- Full traces enable manual cutoff audits.

## Observability

The agent records the shared trace fields plus:

- step number and remaining budget;
- structured plan and selected action;
- action validation result;
- observation identifiers and truncation metadata;
- working-state revision hash;
- stopping reason; and
- forced-finalization status.

The paper must report trajectory length and tool distribution in addition to cost and latency. These mechanism measures help explain whether a result comes from useful adaptation or merely more inference.

## Agent-specific failure modes

- `LOOPING`: semantically repeated actions without material new evidence.
- `QUERY_DRIFT`: investigation moves away from the event and forecast target.
- `UNSUPPORTED_STATE`: working memory contains claims not linked to eligible evidence.
- `PREMATURE_STOP`: finalization occurs with an obviously unresolved high-value question.
- `FORCED_FINALIZATION`: the harness reaches a ceiling and requests an immediate answer.
- `ACTION_SCHEMA_ERROR`: the requested action is not valid.

These are diagnostic labels. The shared evaluator still handles invalid output, timeouts, and budget failures consistently across conditions.

## MVP implementation plan

### P0

1. Reuse the shared schemas, tools, resolver, scorer, and trace format.
2. Implement a deterministic harness that owns state, permissions, budgets, and stopping enforcement.
3. Implement one controller prompt that selects exactly one next action or `FINALIZE`.
4. Add structured working state with evidence provenance.
5. Add loop and query-drift detectors that do not provide extra financial reasoning.
6. Add forced finalization and shared mechanical schema repair.
7. Verify that future-data endpoints are unreachable from the prediction process.
8. Run development-only trajectory audits before freezing prompts and configuration.

### P1

- Retrieve analogous failure cases from shared history.
- Add ablations for history, reflection, and adaptive stopping.
- Study arm-specific self-memory separately from the primary fair comparison.

### P2

- Multi-agent role decomposition.
- Learned retrieval or stopping policies.
- Alternative planning algorithms.

These extensions are excluded from the MVP because they change more than one treatment variable.

## Acceptance criteria

The agent treatment is ready for the pilot only when:

- it consumes the exact shared input and emits the exact shared forecast schema;
- the harness enforces every ceiling without model cooperation;
- every evidence claim can be traced to a cutoff-eligible source;
- future outcome data is inaccessible before resolution;
- identical history snapshot IDs are verified across conditions;
- all actions, observations, costs, and timestamps are logged; and
- forced failures remain visible in the evaluation dataset.
