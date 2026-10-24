from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from domain.models.prediction import Prediction, PredictionDraft, PredictionStatus
from domain.models.reality import Reality
from infra.llm.mock import MockLLMClient
from infra.sources.stock_prices import StockPriceOutcomeResolver
from infra.storage.json_repository import JsonRepository
from service.pipelines.layers.evaluation_layer import EvaluationLayer
from service.pipelines.layers.prediction_layer import PredictionLayer
from service.pipelines.pipeline import MarketHypothesisPipeline
from test_integration import _active_thesis


def fields():
    return dict(target="ACME", metrics=["adjusted_price_return"], direction="UP",
                horizon_start=date(2025, 1, 2), horizon_end=date(2025, 1, 3),
                baseline=100, expected_change_pct=0.03, predicted_drivers=["demand"],
                confidence=0.7, resolution_criteria=["Compare adjusted closes."], reasoning="Demand.")


def prediction(**updates):
    return Prediction(id="p", thesis_id="t", **(fields() | updates))


@pytest.mark.parametrize("model", [PredictionDraft, Prediction])
@pytest.mark.parametrize("direction,magnitude", [("UP", 0.03), ("DOWN", -0.05), ("FLAT", 0), ("UP", 3.0)])
def test_valid_magnitude(model, direction, magnitude):
    data = fields() | dict(direction=direction, expected_change_pct=magnitude)
    if model is Prediction:
        data.update(id="p", thesis_id="t")
    assert model(**data).expected_change_pct == magnitude


@pytest.mark.parametrize("model", [PredictionDraft, Prediction])
@pytest.mark.parametrize("direction,magnitude", [
    ("UP", -0.03), ("DOWN", 0.05), ("FLAT", 0.01), ("UP", 0),
    ("UP", None), ("UP", float("nan")), ("UP", float("inf")), ("DOWN", -float("inf")), ("UP", "bad"),
])
def test_invalid_magnitude(model, direction, magnitude):
    data = fields() | dict(direction=direction, expected_change_pct=magnitude)
    if model is Prediction:
        data.update(id="p", thesis_id="t")
    with pytest.raises(ValidationError):
        model(**data)


def test_required_magnitude():
    data = fields()
    del data["expected_change_pct"]
    with pytest.raises(ValidationError):
        PredictionDraft(**data)


def reality(**updates):
    return Reality(**(dict(id="r", prediction_id="p", target="ACME", metric="adjusted_price_return",
                           baseline=100, actual_value=103, actual_direction="UP",
                           observed_at=datetime(2025, 1, 10, tzinfo=timezone.utc),
                           source="fixture", reasoning="Observed prices.") | updates))


@pytest.mark.parametrize("drivers", [[], ["demand", "guidance"]])
def test_drivers_and_historical_records_roundtrip(tmp_path, drivers):
    repo = JsonRepository(tmp_path / "records.json")
    original = prediction()
    repo.save_many([original, reality(actual_drivers=drivers)])
    loaded = JsonRepository(repo.path)
    assert loaded.get(Prediction, "p") == original
    assert loaded.get(Reality, "r").actual_drivers == drivers
    payload = reality().model_dump()
    del payload["actual_drivers"]
    assert Reality.model_validate(payload).actual_drivers == []


@pytest.mark.parametrize("updates", [
    {"metric": "revenue_growth"}, {"target": "OTHER"}, {"baseline": 101},
    {"observed_at": datetime(2025, 1, 2, tzinfo=timezone.utc)},
])
def test_incompatible_evaluation_does_not_persist(tmp_path, updates):
    repo = JsonRepository(tmp_path / "records.json")
    with pytest.raises(ValueError):
        EvaluationLayer(MockLLMClient(), repo).evaluate(prediction(), reality(**updates))
    assert repo.list(Reality) == []


def test_valid_evaluation_with_later_collection_timestamp(tmp_path):
    repo = JsonRepository(tmp_path / "records.json")
    result = EvaluationLayer(MockLLMClient(), repo).evaluate(prediction(), reality())
    assert result.direction_score == 1
    assert result.reason_score is None
    assert repo.get(Prediction, "p").status == PredictionStatus.RESOLVED


def resolver(tmp_path):
    prices = tmp_path / "prices.csv"
    prices.write_text("ticker,trade_date,close,adj_close\nACME,2025-01-02,100,100\nACME,2025-01-03,103,103\n")
    tickers = tmp_path / "tickers.csv"
    tickers.write_text("ticker,company\nACME,Acme\n")
    return StockPriceOutcomeResolver(prices, tickers)


@pytest.mark.parametrize("updates", [{"metrics": ["revenue_growth"]}, {"baseline": 99}])
def test_price_resolver_rejects_false_contract(tmp_path, updates):
    with pytest.raises(ValueError):
        resolver(tmp_path).resolve(prediction(**updates))


def test_price_resolver_does_not_invent_drivers(tmp_path):
    result = resolver(tmp_path).resolve(prediction())
    assert result.actual_drivers == []
    assert "attribution was not performed" in result.reasoning


def test_pipeline_continues_after_invalid_pair(tmp_path, caplog):
    repo = JsonRepository(tmp_path / "records.json")
    repo.save_many([prediction(metrics=["revenue_growth"]), prediction().model_copy(update={"id": "valid"})])
    pipeline = MarketHypothesisPipeline(source=None, analysis=None, prediction=None, repository=repo,
                                        outcome_resolver=resolver(tmp_path),
                                        evaluation=EvaluationLayer(MockLLMClient(), repo))
    results = pipeline._resolve_due(date(2025, 1, 3), include_same_day=True)
    assert len(results) == 1
    assert results[0].prediction_id == "valid"
    assert "stock-price resolution requires" in caplog.text
    assert repo.get(Prediction, "p").status == PredictionStatus.ACTIVE


def test_large_fraction_is_not_rescaled_and_context_reaches_prompt(tmp_path):
    class LargeMoveLLM(MockLLMClient):
        def generate_response(self, *, system_prompt, response_model):
            response = super().generate_response(system_prompt=system_prompt, response_model=response_model)
            if response_model is PredictionDraft:
                assert '"market_context"' in system_prompt
                return response.model_copy(update={"expected_change_pct": 3.0})
            return response

    repo = JsonRepository(tmp_path / "records.json")
    result = PredictionLayer(LargeMoveLLM(), repo).generate(_active_thesis(repo), market_context={k: fields()[k] for k in ("target", "metrics", "baseline", "horizon_start", "horizon_end")})
    assert result.expected_change_pct == 3.0


@pytest.mark.parametrize("field", ["baseline", "actual_value"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_reality_rejects_nonfinite_values(field, value):
    with pytest.raises(ValidationError):
        reality(**{field: value})


@pytest.mark.parametrize("updates", [
    {"baseline": float("inf")}, {"confidence": float("nan")},
    {"confidence": 1.1}, {"direction": "SIDEWAYS"},
    {"horizon_end": date(2025, 1, 1)},
])
def test_prediction_draft_rejects_invalid_contract(updates):
    with pytest.raises(ValidationError):
        PredictionDraft(**(fields() | updates))


@pytest.mark.parametrize("actual,expected_score", [
    (105, 1.0), (107, 1.0), (107.001, 0.5),
    (110, 0.5), (110.001, 0.0), (95, 0.0),
])
@pytest.mark.parametrize("llm_score", [None, 0.0, 1.0])
def test_magnitude_is_computed_by_code(tmp_path, actual, expected_score, llm_score):
    from domain.models.evaluation import EvaluationDraft

    class WrongMagnitudeLLM(MockLLMClient):
        def generate_response(self, *, system_prompt, response_model):
            assert '"computed_magnitude_score"' in system_prompt
            return EvaluationDraft(direction_score=1, magnitude_score=llm_score,
                                   explanation="Direction assessed.")

    repo = JsonRepository(tmp_path / "records.json")
    result = EvaluationLayer(WrongMagnitudeLLM(), repo).evaluate(
        prediction(expected_change_pct=0.05),
        reality(actual_value=actual, actual_direction="UP" if actual > 100 else "DOWN"),
    )
    assert result.magnitude_score == expected_score
    assert result.matching_score == pytest.approx((1 + expected_score) / 2)
    assert "Magnitude calculated by code" in result.explanation
    assert JsonRepository(repo.path).get(type(result), result.id).magnitude_score == expected_score
