import argparse
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from domain.models.event import Event
from domain.models.prediction import Direction
from domain.models.reality import Reality
from infra.llm.mock import MockLLMClient
from infra.sources.in_memory import InMemorySourceAdapter
from infra.storage.json_repository import JsonRepository
from service.pipelines.layers.analysis_layer import AnalysisLayer
from service.pipelines.layers.evaluation_layer import EvaluationLayer
from service.pipelines.layers.prediction_layer import PredictionLayer
from service.pipelines.pipeline import MarketHypothesisPipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic end-to-end contract demo.")
    parser.add_argument("--data-dir", default="data_storage", help="Directory for JSON persistence.")
    args = parser.parse_args()

    event = Event(
        id="demo-acme-guidance",
        source="demo fixture",
        title="ACME raises revenue guidance after strong demand",
        content="ACME reports demand growth and raises full-year revenue guidance.",
        companies_mentioned=["ACME"],
    )
    repository = JsonRepository(Path(args.data_dir) / "records.json")
    llm = MockLLMClient()
    pipeline = MarketHypothesisPipeline(
        source=InMemorySourceAdapter([event]),
        analysis=AnalysisLayer(llm, repository),
        prediction=PredictionLayer(llm, repository),
        repository=repository,
    )

    [result] = pipeline.run("ACME guidance", limit=1)
    assert result.thesis is not None and result.prediction is not None
    print(f"Event {result.event.id} -> Thesis {result.thesis.id} -> Prediction {result.prediction.id} v{result.prediction.version}")

    actual_change = result.prediction.expected_change_pct
    actual_direction = Direction.UP if actual_change > 0 else Direction.DOWN if actual_change < 0 else Direction.FLAT
    observed_at = datetime.combine(result.prediction.horizon_end + timedelta(days=1), time.min, tzinfo=timezone.utc)
    reality = Reality(
        id=f"reality-{result.prediction.id}",
        prediction_id=result.prediction.id,
        target=result.prediction.target,
        metric=result.prediction.metrics[0],
        baseline=result.prediction.baseline,
        actual_value=result.prediction.baseline * (1 + actual_change),
        actual_direction=actual_direction,
        observed_at=observed_at,
        source="demo fixture",
        reasoning="Synthetic outcome used only to verify the evaluation contract.",
        actual_drivers=result.prediction.predicted_drivers,
    )
    evaluation = EvaluationLayer(llm, repository).evaluate(result.prediction, reality)
    print(f"Evaluation {evaluation.id}: matching_score={evaluation.matching_score:.2f}; result persisted to {args.data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
