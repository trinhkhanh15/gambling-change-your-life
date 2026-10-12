from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path

from domain.models.evaluation import Evaluation
from domain.models.prediction import Prediction
from domain.models.reality import Reality
from infra.llm.mock import MockLLMClient
from infra.sources.csv_events import CsvEventSourceAdapter
from infra.sources.stock_prices import StockPriceOutcomeResolver
from infra.storage.json_repository import JsonRepository
from service.pipelines.layers.analysis_layer import AnalysisLayer
from service.pipelines.layers.evaluation_layer import EvaluationLayer
from service.pipelines.layers.prediction_layer import PredictionLayer
from service.pipelines.pipeline import MarketHypothesisPipeline, PipelineResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay news CSV events through analysis, prediction, market resolution, and feedback."
    )
    parser.add_argument("--events", type=Path, default=Path("data/raw_news_websearch"))
    parser.add_argument("--prices", type=Path, default=Path("data/market/stock_prices_daily.csv"))
    parser.add_argument("--tickers", type=Path, default=Path("data/stock_tickers.csv"))
    parser.add_argument("--query", default="", help="Optional case-insensitive article text filter")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--data-dir", type=Path, default=Path("data_storage/e2e"))
    parser.add_argument("--openai", action="store_true", help="Use OpenAI instead of the deterministic mock")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    for path in (args.events, args.prices, args.tickers):
        if not path.exists():
            raise SystemExit(f"Required input does not exist: {path}")

    llm = MockLLMClient()
    if args.openai:
        from infra.llm.openai_adapter import OpenAIAdapter

        llm = OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))
        llm_label = f"OpenAI / {llm.model_name}"
    else:
        llm_label = "MockLLMClient (deterministic)"

    repository = JsonRepository(args.data_dir / "records.json")
    source = CsvEventSourceAdapter(args.events, args.tickers)
    outcomes = StockPriceOutcomeResolver(args.prices, args.tickers)
    pipeline = MarketHypothesisPipeline(
        source=source,
        analysis=AnalysisLayer(llm, repository),
        prediction=PredictionLayer(llm, repository),
        repository=repository,
        outcome_resolver=outcomes,
        evaluation=EvaluationLayer(repository),
    )

    previous_evaluation_ids = {item.id for item in repository.list(Evaluation)}
    previous_prediction_ids = {item.id for item in repository.list(Prediction)}
    _print_run_header(args, llm_label)
    results = pipeline.run(args.query, limit=args.limit)
    predictions = repository.list(Prediction)
    evaluations = repository.list(Evaluation)
    realities = {item.id: item for item in repository.list(Reality)}
    run_prediction_ids = {
        result.prediction.id for result in results if result.prediction is not None
    }
    linked_evaluations = [
        item for item in evaluations
        if item.id not in previous_evaluation_ids or item.prediction_id in run_prediction_ids
    ]
    new_evaluations = [item for item in evaluations if item.id not in previous_evaluation_ids]
    prediction_by_id = {item.id: item for item in predictions}
    evaluation_by_prediction: dict[str, Evaluation] = {}
    for evaluation in evaluations:
        current = evaluation_by_prediction.get(evaluation.prediction_id)
        if current is None or current.evaluated_at < evaluation.evaluated_at:
            evaluation_by_prediction[evaluation.prediction_id] = evaluation

    printed_evaluation_for_prediction: dict[str, int] = {}
    for index, result in enumerate(results, start=1):
        _print_event_trace(
            index=index,
            result=result,
            resolver=outcomes,
            prediction_by_id=prediction_by_id,
            evaluation_by_prediction=evaluation_by_prediction,
            realities=realities,
            new_evaluation_ids={item.id for item in new_evaluations},
            printed_evaluation_for_prediction=printed_evaluation_for_prediction,
        )

    _print_resolutions_not_in_replay(
        new_evaluations,
        run_prediction_ids=run_prediction_ids,
        prediction_by_id=prediction_by_id,
        realities=realities,
    )
    _print_run_summary(
        results=results,
        predictions=predictions,
        previous_prediction_ids=previous_prediction_ids,
        new_evaluations=new_evaluations,
        linked_evaluations=linked_evaluations,
        llm_label=llm_label,
        storage_path=repository.path,
    )
    _print_optimization_questions()
    return 0 if run_prediction_ids and linked_evaluations else 2


def _print_run_header(args: argparse.Namespace, llm_label: str) -> None:
    print("=" * 88)
    print("CSV FEEDBACK REPLAY — RUN CONFIGURATION")
    print(f"LLM:       {llm_label}")
    print(f"Events:    {args.events}")
    print(f"Prices:    {args.prices}")
    print(f"Tickers:   {args.tickers}")
    print(f"Query:     {args.query or '(none; all articles)'}")
    print(f"Limit:     {args.limit}")
    print(f"Data dir:  {args.data_dir}")
    print("=" * 88)


def _print_event_trace(
    *,
    index: int,
    result: PipelineResult,
    resolver: StockPriceOutcomeResolver,
    prediction_by_id: dict[str, Prediction],
    evaluation_by_prediction: dict[str, Evaluation],
    realities: dict[str, Reality],
    new_evaluation_ids: set[str],
    printed_evaluation_for_prediction: dict[str, int],
) -> None:
    event = result.event
    thesis = result.thesis
    prediction = result.prediction
    print(f"\n[{index}] EVENT")
    print(f"  id:         {event.id}")
    print(f"  published:  {event.published_at.isoformat()}")
    print(f"  source:     {event.source}")
    print(f"  title:      {event.title}")
    print(f"  companies:  {', '.join(event.companies_mentioned) or '(none detected)'}")

    print("  ROUTER")
    print(f"    action:   {result.decision.action.value}")
    print(f"    target:   {result.decision.target_thesis_id or '(none)'}")
    print(f"    reason:   {result.decision.reasoning}")

    if thesis is None:
        print("  THESIS:     (no thesis returned by router)")
    else:
        current_evidence = [item.point for item in thesis.evidence if item.event_id == event.id]
        current_counter_evidence = [
            item.point for item in thesis.counter_evidence if item.event_id == event.id
        ]
        print("  THESIS")
        print(f"    id/ticker: {thesis.id} / {thesis.ticker}")
        print(f"    state:     {thesis.status.value}, strength={thesis.strength:.2f}")
        print(f"    claim:     {thesis.core_claim}")
        print(f"    reasoning: {thesis.reasoning}")
        _print_items("evidence added from this event", current_evidence)
        _print_items("counter-evidence added from this event", current_counter_evidence)
        if thesis.kill_reason:
            print(f"    kill reason: {thesis.kill_reason}")

        detected_tickers = {
            ticker
            for company in event.companies_mentioned
            if (ticker := resolver.canonical_ticker(company)) is not None
        }
        thesis_ticker = resolver.canonical_ticker(thesis.ticker) or thesis.ticker.upper()
        if detected_tickers and thesis_ticker not in detected_tickers:
            print(
                "  WARNING: thesis ticker is not among the event's detected companies; "
                f"review routing (detected={', '.join(sorted(detected_tickers))}, "
                f"thesis={thesis_ticker})."
            )
        elif len(detected_tickers) > 1:
            print(
                "  REVIEW: event mentions multiple detected tickers; "
                f"router selected {thesis_ticker} from {', '.join(sorted(detected_tickers))}."
            )
        elif not detected_tickers:
            print("  REVIEW: event has no detected company ticker to compare with this thesis.")

    if prediction is None:
        if result.decision.action.value == "IGNORE":
            reason = "router chose IGNORE"
        elif thesis is not None and thesis.status.value == "KILLED":
            reason = "thesis is killed"
        elif thesis is not None:
            detail = resolver.forecast_context_diagnostic(thesis.ticker, event.published_at)
            reason = f"no usable market window was available for prediction: {detail}"
        else:
            reason = "no active thesis was returned"
        print(f"  PREDICTION: (none; {reason})")
        return

    stored_prediction = prediction_by_id.get(prediction.id, prediction)
    reused = stored_prediction.information_cutoff < event.published_at
    print("  PREDICTION")
    print(f"    id/status: {stored_prediction.id} / {stored_prediction.status.value}")
    print(f"    target:    {stored_prediction.target} | metric={', '.join(stored_prediction.metrics)}")
    print(
        f"    forecast:  {stored_prediction.direction.value} "
        f"{stored_prediction.expected_change_pct * 100:+.2f}% | "
        f"confidence={stored_prediction.confidence:.2f}"
    )
    print(
        f"    market:    baseline={stored_prediction.baseline:.4f} "
        f"on {stored_prediction.horizon_start} -> horizon end {stored_prediction.horizon_end}"
    )
    print(f"    cutoff:    {stored_prediction.information_cutoff.isoformat()}")
    print(f"    reasoning: {stored_prediction.reasoning}")
    _print_items("predicted drivers", stored_prediction.predicted_drivers)
    if reused:
        print("    note:      existing active prediction reused; no new prediction was generated here")
    if (stored_prediction.horizon_end - stored_prediction.horizon_start).days > 10:
        print(
            "  WARNING: baseline-to-horizon span exceeds 10 calendar days; "
            "inspect trading-date coverage before treating this as five sessions."
        )

    evaluation = evaluation_by_prediction.get(stored_prediction.id)
    if evaluation is None:
        latest_price_date = resolver.latest_date
        if latest_price_date is None or stored_prediction.horizon_end > latest_price_date:
            detail = f"waiting for horizon; latest price date is {latest_price_date or '(none)'}"
        elif resolver.resolve(stored_prediction) is None:
            detail = "horizon date passed available data, but an exact target/baseline/horizon price row is missing"
        else:
            detail = "reality is resolvable but no evaluation record was found; inspect persisted records"
        print(f"  EVALUATION: no evaluation record yet ({detail})")
        return
    earlier_event_index = printed_evaluation_for_prediction.get(stored_prediction.id)
    if earlier_event_index is not None:
        print(
            "  EVALUATION: same prediction as event "
            f"[{earlier_event_index}]; see its evaluation block above."
        )
        return
    printed_evaluation_for_prediction[stored_prediction.id] = index

    reality = realities.get(evaluation.reality_id)
    freshness = "new this run" if evaluation.id in new_evaluation_ids else "already persisted"
    if reality is not None and reality.observed_at > event.published_at:
        freshness += f"; resolved later at {reality.observed_at.isoformat()}"
    print(f"  EVALUATION ({freshness})")
    print(
        f"    scores: direction={evaluation.direction_score:.3f}, "
        f"magnitude={evaluation.magnitude_score:.3f}, "
        f"drivers={evaluation.reason_score if evaluation.reason_score is not None else 'not assessed'}, "
        f"matching={evaluation.matching_score:.3f}"
    )
    print(f"    explanation: {evaluation.explanation}")
    if reality is not None:
        print(
            f"    observed: {reality.actual_direction.value} "
            f"{reality.actual_change_pct * 100:+.2f}% at {reality.observed_at.isoformat()} "
            f"(value={reality.actual_value:.4f}, source={reality.source})"
        )


def _print_items(label: str, values: list[str]) -> None:
    if not values:
        print(f"    {label}: (none)")
        return
    print(f"    {label}:")
    for value in values:
        print(f"      - {value}")


def _print_resolutions_not_in_replay(
    evaluations: list[Evaluation],
    *,
    run_prediction_ids: set[str],
    prediction_by_id: dict[str, Prediction],
    realities: dict[str, Reality],
) -> None:
    other_evaluations = [item for item in evaluations if item.prediction_id not in run_prediction_ids]
    if not other_evaluations:
        return
    print("\nRESOLUTIONS OF OLDER PREDICTIONS THIS RUN")
    for evaluation in other_evaluations:
        prediction = prediction_by_id.get(evaluation.prediction_id)
        reality = realities.get(evaluation.reality_id)
        target = prediction.target if prediction is not None else "unknown target"
        outcome = (
            f"{reality.actual_direction.value} {reality.actual_change_pct * 100:+.2f}%"
            if reality is not None
            else "reality record missing"
        )
        print(
            f"  prediction={evaluation.prediction_id} target={target} outcome={outcome} "
            f"matching={evaluation.matching_score:.3f}"
        )


def _print_run_summary(
    *,
    results: list[PipelineResult],
    predictions: list[Prediction],
    previous_prediction_ids: set[str],
    new_evaluations: list[Evaluation],
    linked_evaluations: list[Evaluation],
    llm_label: str,
    storage_path: Path,
) -> None:
    actions = Counter(result.decision.action.value for result in results)
    replay_prediction_ids = {
        result.prediction.id for result in results if result.prediction is not None
    }
    created_prediction_ids = {
        prediction.id for prediction in predictions
        if prediction.id not in previous_prediction_ids
    }
    print("\n" + "=" * 88)
    print("RUN SUMMARY")
    print(f"  events processed:                 {len(results)}")
    print(f"  router actions:                   {dict(sorted(actions.items())) or '(none)'}")
    print(f"  unique predictions in this replay:{len(replay_prediction_ids):>7}")
    print(f"  predictions newly created:        {len(created_prediction_ids)}")
    print(f"  evaluations created this run:     {len(new_evaluations)}")
    print(f"  evaluations linked to this replay:{len(linked_evaluations):>7}")
    print(f"  LLM:                              {llm_label}")
    print(f"  records:                          {storage_path}")
    passed = bool(replay_prediction_ids and linked_evaluations)
    print(f"  E2E completion:                   {'passed' if passed else 'incomplete'} (exit {0 if passed else 2})")
    print("  Matching score is a pipeline diagnostic, not standalone forecast accuracy.")
    print("=" * 88)


def _print_optimization_questions() -> None:
    questions = [
        "Ở lớp nào nên chặn một event bị gắn vào thesis có ticker không liên quan?",
        "Làm sao xác nhận horizon là đúng 5 phiên giao dịch khi CSV thiếu ngày giá?",
        "Matching score đang trộn những tín hiệu nào; nên tách thêm metric nào để đo forecast?",
        "Lần tối ưu tiếp theo sẽ thay đổi đúng một giả thuyết nào, và dùng baseline/holdout nào để so?",
    ]
    print("\nCÂU HỎI CHO VÒNG TỐI ƯU TIẾP THEO")
    for index, question in enumerate(questions, start=1):
        print(f"  {index}. {question}")


if __name__ == "__main__":
    raise SystemExit(main())
