# MVP Architecture — Financial Research Agent

## Note

`P0` means the task is critical and must be done in the first iteration.

`P1` means the task is important but not critical.

`P2` means the task is nice to have.

The system follows a continuous loop:

**Events → Thesis Analysis → Prediction → Reality → Evaluation → Feedback**

The objective is to build an AI-native research system that maintains and updates theses and predictions over time, rather than generating isolated predictions from individual news articles.

## 1. Event Layer

This layer is responsible for collecting and structuring information that can be used to update theses and evaluate predictions.

* **P0:** Pull events from various sources, including news, reports, company disclosures, and market data.
* **P0:** Convert events into a standard format for further processing.
* **P0:** Preserve the source, timestamp, and relevant factual information so that downstream layers can trace evidence back to its origin.
* **P0:** Classify events by:

  * `nature`: fact / expectation
  * `scope`: company / industry / macro
* **P1:** Combine related events to generate a more comprehensive view of the current situation. A single event may not provide enough context to determine which thesis is relevant or how it should be updated.
* **P1:** Use embedding/top-k retrieval to find the most relevant events for a given thesis.

**Output:** Structured events that can be consumed by the Analysis Layer and the Resolution & Feedback Layer.

## 2. Analysis Layer

This layer is responsible for maintaining theses based on new evidence.

### Thesis Routing

* **P0:** Analyze incoming events and route them to `UPDATE_THESIS`, `GENERATE_THESIS`, or `IGNORE`.
* **P0:** Determine whether an event supports an existing thesis, contradicts it, introduces a genuinely new thesis, or is irrelevant.

### UPDATE_THESIS

* **P0:** Update evidence and counter-evidence for existing theses.
* **P0:** Update thesis reasoning and strength based on the new evidence.
* **P0:** Decide whether the thesis should remain active or be killed.

**Rules:**

* The core thesis content remains unchanged. Evidence, counter-evidence, reasoning, and strength are dynamic.
* If new information requires changing the core claim, the system should generate a new thesis rather than silently rewriting the existing one.
* `strength` represents how strongly the current evidence supports the thesis. It is separate from prediction confidence.
* Thesis kill decisions must be based on evidence and the validity of core assumptions, not directly on prediction confidence or a single matching score.
* Strength updates and kill decisions must include reasoning. The initial implementation may use simple, explicit rules; more sophisticated scoring can be introduced after evaluation data is available.

### GENERATE_THESIS

* **P0:** Generate new theses based on the events.
* **P0:** Define the core claim, supporting reasoning, evidence, counter-evidence, and initial strength.
* **P0:** Avoid generating duplicate theses when an existing thesis can be updated.

**Output:** Updated or newly generated theses with their current evidence, reasoning, strength, and lifecycle status.

## 3. Prediction Layer

This layer is responsible for generating and maintaining predictions derived from theses and their evidence.

### Prediction Routing

* **P0:** Route to `UPDATE_PREDICTION` or `GENERATE_PREDICTION` based on the updated analysis.
* **P0:** Allow the system to keep an existing prediction unchanged when new information does not materially affect it.

### UPDATE_PREDICTION

* **P0:** Update prediction reasoning and confidence based on new evidence, counter-evidence, and changes in market expectations.
* **P0:** If the forecast itself changes materially, create a new prediction version and supersede the previous version rather than overwriting it.

**Rules:**

* Prediction confidence represents the model's confidence in the prediction. It is primarily used in the feedback loop to evaluate calibration.
* A new prediction does not make the previous prediction wrong. It represents an updated belief based on a different information set.
* Previous prediction versions must remain available for evaluation against reality.
* Analysis may supersede a prediction, but it must not mark a prediction as correct or incorrect. That requires resolution against reality.

### GENERATE_PREDICTION

* **P0:** Generate predictions based on theses, evidence, counter-evidence, and current market expectations.
* **P0:** Every prediction must define a testable outcome, including:

  * Target and metric
  * Predicted direction or value
  * Time horizon
  * Reference point or baseline, where applicable
  * Resolution criteria
* **P0:** Store the prediction's reasoning, confidence, creation time, and information cutoff.

A prediction that cannot be evaluated against an observable outcome should not be treated as a valid forecast.

### Market Expectation Reasoning

* **P0:** Consider both fundamentals and market expectations when generating predictions. The system should distinguish between what is happening and what the market already expects to happen.
* **P1:** Limit the depth of self-asking questions about game theory, such as “what does the market think other market participants are thinking?”, to avoid unnecessary reasoning and irrelevant speculation.

**Important:** Market prices reflect expectations about future outcomes, not simply current reality. The relevant question is often how new information changes expectations relative to what was already priced in. However, not every prediction requires game-theoretic reasoning; the system should use it when relevant rather than forcing it into every analysis.

**Output:** Active predictions and immutable historical prediction versions.

## 4. Resolution & Feedback Layer

This layer is responsible for evaluating predictions against reality and using the results to improve the prediction system.

### Prediction Resolution

* **P0:** Identify predictions that have reached their evaluation horizon or whose resolution conditions have been met.
* **P0:** Retrieve the relevant reality data from the Event Layer or other appropriate data sources.
* **P0:** Match reality data against the prediction's predefined target, metric, horizon, and resolution criteria.
* **P0:** Determine whether sufficient information is available to evaluate the prediction.

**Rules:**

* Not every event can validate a prediction. An event may update a thesis without providing the observable outcome required to resolve a prediction.
* A prediction about a future earnings metric should be evaluated against the relevant reported metric.
* A prediction about a stock's return over a specified period should be evaluated against the appropriate market price data.
* Prediction versions must be evaluated using their original forecasts and information cutoffs. Historical forecasts must not be overwritten by later revisions.

### Prediction Evaluation

* **P0:** Calculate a matching score or another appropriate evaluation metric by comparing the stored prediction with reality.
* **P0:** Store the evaluation result together with the prediction, reality data, and reasoning for the score.
* **P0:** Evaluate prediction confidence against actual outcomes to identify overconfidence, underconfidence, and other calibration problems.
* **P0:** Preserve the distinction between prediction error and thesis invalidation. A failed prediction does not automatically imply that its underlying thesis should be killed.

### Feedback Loop 

* **P0:** Use evaluation results to identify recurring prediction errors and improve future prediction generation and confidence calibration.
* **P0:** Store relevant failure cases, including the original prediction, reality, mismatch, and possible reasons for the error.
* **P1:** Retrieve relevant historical failure cases when generating new predictions.
* **P1:** Analyze whether recurring errors originate from thesis reasoning, expectation modeling, prediction generation, or confidence calibration.

**Output:** Resolved prediction records, evaluation metrics, and feedback data for future improvement.

## Prediction Lifecycle

```text
GENERATE
    ↓
ACTIVE
    ├── New evidence → KEEP
    ├── New evidence → SUPERSEDE → New prediction version
    └── Horizon / resolution condition reached
                              ↓
                           RESOLVE
                              ↓
                           EVALUATE
                              ↓
                           FEEDBACK
```

`SUPERSEDED` means the prediction is no longer the system's current forecast. It does not mean the prediction was wrong.

`RESOLVED` means sufficient reality data is available to evaluate the prediction.

Historical prediction versions must remain available for evaluation, even after they have been superseded.

## MVP Scope

The first iteration should prioritize a working end-to-end loop over sophisticated scoring, complex retrieval, or advanced game-theoretic reasoning.

The minimum successful system should be able to:

**Collect events → Maintain theses → Generate testable predictions → Update predictions without losing history → Resolve predictions against reality → Evaluate confidence and prediction quality.**

More advanced retrieval, scoring, and improvement mechanisms should be added only after the basic loop works and produces useful evaluation data.
