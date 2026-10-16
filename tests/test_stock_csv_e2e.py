from datetime import date, datetime, timezone

from domain.models.evaluation import Evaluation
from domain.models.prediction import Direction, Prediction, PredictionStatus
from domain.models.reality import Reality
from domain.models.thesis import Thesis
from infra.llm.mock import MockLLMClient
from infra.sources.csv_events import CsvEventSourceAdapter
from infra.sources.stock_prices import StockPriceOutcomeResolver
from infra.storage.json_repository import JsonRepository
from service.pipelines.layers.analysis_layer import AnalysisLayer
from service.pipelines.layers.evaluation_layer import EvaluationLayer
from service.pipelines.layers.prediction_layer import PredictionLayer
from service.pipelines.pipeline import MarketHypothesisPipeline


class RecordingMockLLMClient(MockLLMClient):
    def __init__(self):
        self.prompts: list[str] = []

    def generate_response(self, *, system_prompt: str, response_model):
        self.prompts.append(system_prompt)
        return super().generate_response(system_prompt=system_prompt, response_model=response_model)


def test_news_csv_resolves_prices_and_feedback_reaches_next_analysis(tmp_path):
    events_path = tmp_path / "events.csv"
    events_path.write_text(
        "published_at,title,content,source\n"
        '"Fri, 03 Jan 2025 08:00:00 GMT","ACME raises guidance","ACME demand increased","news.test/acme-1"\n'
        '"Mon, 06 Jan 2025 08:00:00 GMT","ACME reports orders","ACME demand remains strong","news.test/acme-2"\n'
        '"Fri, 10 Jan 2025 08:00:00 GMT","ACME expands production","ACME confirms more demand","news.test/acme-3"\n',
        encoding="utf-8",
    )
    tickers_path = tmp_path / "tickers.csv"
    tickers_path.write_text(
        "ticker,company,domain,currency\nACME,ACME,technology,USD\n",
        encoding="utf-8",
    )
    prices_path = tmp_path / "prices.csv"
    prices_path.write_text(
        "ticker,company,domain,trade_date,close,adj_close\n"
        "ACME,Acme,technology,2025-01-02,100,100\n"
        "ACME,Acme,technology,2025-01-03,101,101\n"
        "ACME,Acme,technology,2025-01-06,102,102\n"
        "ACME,Acme,technology,2025-01-07,103,103\n"
        "ACME,Acme,technology,2025-01-08,104,104\n"
        "ACME,Acme,technology,2025-01-09,105,105\n"
        "ACME,Acme,technology,2025-01-10,106,106\n"
        "ACME,Acme,technology,2025-01-13,107,107\n"
        "ACME,Acme,technology,2025-01-14,108,108\n"
        "ACME,Acme,technology,2025-01-15,109,109\n"
        "ACME,Acme,technology,2025-01-16,110,110\n",
        encoding="utf-8",
    )

    repository = JsonRepository(tmp_path / "records.json")
    llm = RecordingMockLLMClient()
    pipeline = MarketHypothesisPipeline(
        source=CsvEventSourceAdapter(events_path, tickers_path),
        analysis=AnalysisLayer(llm, repository),
        prediction=PredictionLayer(llm, repository),
        repository=repository,
        outcome_resolver=StockPriceOutcomeResolver(prices_path, tickers_path),
        evaluation=EvaluationLayer(llm, repository),
    )

    results = pipeline.run("", limit=3)

    assert len(results) == 3
    assert all(result.prediction is not None for result in results)
    assert results[0].event.published_at.date() == date(2025, 1, 3)
    assert results[0].prediction.target == "ACME"
    assert results[0].prediction.baseline == 100
    assert results[0].prediction.horizon_end == date(2025, 1, 9)
    assert results[0].prediction.information_cutoff == results[0].event.published_at
    assert results[0].prediction.id == results[1].prediction.id
    assert results[2].prediction.id != results[1].prediction.id

    predictions = repository.list(Prediction)
    evaluations = repository.list(Evaluation)
    assert len(evaluations) == 2
    assert all(item.status == PredictionStatus.RESOLVED for item in predictions)
    assert any(
        '"recent_resolved_feedback"' in prompt and '"matching_score"' in prompt
        for prompt in llm.prompts
    )


def test_analysis_does_not_receive_outcomes_from_after_event_cutoff(tmp_path):
    repository = JsonRepository(tmp_path / "records.json")
    thesis = Thesis(
        id="thesis-acme",
        ticker="ACME",
        core_claim="Demand remains strong.",
        core_assumptions=["Demand persists."],
        strength=0.7,
        reasoning="Fixture thesis.",
    )
    prediction = Prediction(
        id="prediction-acme",
        thesis_id=thesis.id,
        target="ACME",
        metrics=["adjusted_price_return"],
        direction=Direction.UP,
        horizon_start=date(2025, 1, 2),
        horizon_end=date(2025, 1, 9),
        baseline=100,
        expected_change_pct=0.05,
        predicted_drivers=["demand"],
        confidence=0.65,
        resolution_criteria=["Compare adjusted closes."],
        reasoning="Fixture prediction.",
    )
    reality = Reality(
        id="reality-acme",
        prediction_id=prediction.id,
        target="ACME",
        metric="adjusted_price_return",
        baseline=100,
        actual_value=105,
        actual_direction=Direction.UP,
        observed_at=datetime(2025, 1, 12, tzinfo=timezone.utc),
        source="fixture",
        reasoning="Fixture outcome.",
    )
    evaluation = Evaluation(
        id="evaluation-acme",
        prediction_id=prediction.id,
        prediction_version=1,
        reality_id=reality.id,
        direction_score=1,
        magnitude_score=1,
        matching_score=1,
        explanation="Fixture score.",
    )
    repository.save_many([thesis, prediction, reality, evaluation])

    feedback = AnalysisLayer(MockLLMClient(), repository)._recent_feedback(
        as_of=datetime(2025, 1, 10, tzinfo=timezone.utc)
    )

    assert feedback == []
