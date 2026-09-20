from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from domain.models.feedback import Reality
from domain.models.prediction import Prediction, PredictionDirection, PredictionStatus
from service.pipelines.evaluation_service import (
    DEFAULT_MAGNITUDE_TOLERANCE,
    calculate_direction_score,
    calculate_magnitude_score,
    calculate_matching_score,
    calculate_reason_score,
)
from service.pipelines.prediction_service import PredictionService


class FakeAnalysisOutput:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_direction_score_cases():
    assert calculate_direction_score(PredictionDirection.UP, PredictionDirection.UP) == 1.0
    assert calculate_direction_score(PredictionDirection.UP, PredictionDirection.DOWN) == 0.0
    assert calculate_direction_score(PredictionDirection.UP, PredictionDirection.FLAT) == 0.5


def test_magnitude_score_cases():
    assert calculate_magnitude_score(0.10, 0.10) == 1.0
    assert calculate_magnitude_score(0.10, 0.12, tolerance=DEFAULT_MAGNITUDE_TOLERANCE) == pytest.approx(0.90)
    assert calculate_magnitude_score(0.10, 0.30, tolerance=DEFAULT_MAGNITUDE_TOLERANCE) == pytest.approx(0.0)

    with pytest.raises(ValueError):
        calculate_magnitude_score(0.10, 0.12, tolerance=0.0)


def test_reason_score_cases():
    assert calculate_reason_score(["subscriber_growth", "pricing"], ["pricing", "advertising"]) == pytest.approx(1 / 3)
    assert calculate_reason_score(["a", "b"], ["a", "b"]) == 1.0
    assert calculate_reason_score(["a", "b"], ["c", "d"]) == 0.0
    assert calculate_reason_score(["a", "b"], []) is None


def test_matching_score_all_scores_available():
    score = calculate_matching_score(1.0, 0.9, 1 / 3)
    assert score == pytest.approx(76.96, abs=0.1)


def test_matching_score_missing_reason_reweights():
    assert calculate_matching_score(1.0, 0.9, None) == pytest.approx(94.87, abs=0.1)


def test_invalid_score_inputs_raise():
    with pytest.raises(ValueError):
        calculate_matching_score(1.5, 0.8, 0.3)
    with pytest.raises(ValueError):
        calculate_matching_score(0.7, 1.2, None)


def test_prediction_versioning_and_status():
    service = PredictionService()

    first = Prediction(
        id="pred-1",
        thesis_id="thesis-1",
        version=1,
        target="AAPL",
        metrics=["revenue_growth"],
        direction=PredictionDirection.UP,
        horizon_start=date(2026, 10, 1),
        horizon_end=date(2026, 12, 31),
        baseline=0.02,
        reasoning="Revenue is accelerating.",
        predicted_drivers=["demand", "pricing"],
        confidence=0.7,
        resolution_criteria=["Revenue growth exceeds 5% QoQ after report."],
        status=PredictionStatus.ACTIVE,
        information_cutoff=datetime.utcnow(),
    )
    service._persist_prediction(first)

    second = Prediction(
        id="pred-2",
        thesis_id="thesis-1",
        version=2,
        target="AAPL",
        metrics=["revenue_growth"],
        direction=PredictionDirection.UP,
        horizon_start=date(2026, 10, 1),
        horizon_end=date(2026, 12, 31),
        baseline=0.02,
        reasoning="Demand remains strong.",
        predicted_drivers=["demand", "pricing"],
        confidence=0.8,
        resolution_criteria=["Revenue growth exceeds 5% QoQ after report."],
        status=PredictionStatus.ACTIVE,
        information_cutoff=datetime.utcnow(),
    )
    service._persist_prediction(second)

    assert first.status == PredictionStatus.SUPERSEDED
    assert second.status == PredictionStatus.ACTIVE
    assert len(service.predictions) == 2


def test_prediction_validation_rejects_invalid_values():
    with pytest.raises(ValidationError):
        Prediction.model_validate(
            {
                "id": "pred-3",
                "thesis_id": "thesis-1",
                "version": 1,
                "target": "",
                "metrics": ["revenue_growth"],
                "direction": "UP",
                "horizon_start": date(2026, 10, 1),
                "horizon_end": date(2026, 12, 31),
                "baseline": 0.0,
                "reasoning": "Reasoning",
                "predicted_drivers": ["demand"],
                "confidence": 1.5,
                "resolution_criteria": ["must be measurable"],
                "status": "ACTIVE",
                "information_cutoff": datetime.utcnow(),
            }
        )


def test_llm_prediction_is_created_from_mocked_response():
    service = PredictionService(llm_client=None)

    analysis = FakeAnalysisOutput(
        thesis_id="thesis-1",
        target="AAPL",
        metrics=["revenue_growth"],
        direction="UP",
        horizon_start=date(2026, 10, 1),
        horizon_end=date(2026, 12, 31),
        baseline=0.03,
        reasoning="Demand is accelerating.",
        predicted_drivers=["demand", "pricing"],
        confidence=0.8,
        resolution_criteria=["Revenue growth exceeds 5% QoQ after the report."],
        information_cutoff=datetime.utcnow(),
    )

    class MockLLM:
        def generate_response(self, system_prompt: str, response_model=None):
            return {
                "target": "AAPL",
                "metrics": ["revenue_growth"],
                "direction": "UP",
                "horizon_start": "2026-10-01",
                "horizon_end": "2026-12-31",
                "baseline": 0.03,
                "reasoning": "Demand is accelerating.",
                "predicted_drivers": ["demand", "pricing"],
                "confidence": 0.8,
                "resolution_criteria": ["Revenue growth exceeds 5% QoQ after the report."],
            }

    service.llm = MockLLM()
    prediction = service.generate(analysis)

    assert prediction.target == "AAPL"
    assert prediction.version == 1
    assert prediction.direction == PredictionDirection.UP
    assert prediction.status == PredictionStatus.ACTIVE


def test_reality_model_and_matching_score_input_validation():
    reality = Reality(
        target="AAPL",
        metric="revenue_growth",
        actual_value=0.12,
        actual_direction="UP",
        observed_at=datetime.utcnow(),
        source="earnings_release",
        reasoning="Revenue grew faster than forecast.",
        actual_drivers=["pricing", "demand"],
    )

    assert reality.actual_direction == "UP"
    assert reality.target == "AAPL"


def test_llm_comparison_creates_new_version_when_requested():
    service = PredictionService()
    now = datetime.utcnow()
    first = Prediction(
        id="pred-1",
        thesis_id="thesis-1",
        version=1,
        target="AAPL",
        direction=PredictionDirection.UP,
        horizon_start=date(2026, 10, 1),
        horizon_end=date(2026, 12, 31),
        reasoning="Demand is accelerating.",
        confidence=0.7,
        created_at=now,
        information_cutoff=now,
    )
    service._persist_prediction(first)

    class MockLLM:
        def __init__(self):
            self.calls = 0

        def generate_response(self, system_prompt: str, response_model=None):
            self.calls += 1
            if response_model.__name__ == "PredictionLLMOutput":
                return {
                    "target": "AAPL",
                    "direction": "DOWN",
                    "horizon_start": "2026-10-01",
                    "horizon_end": "2026-12-31",
                    "reasoning": "Demand is weakening.",
                    "confidence": 0.6,
                }
            return {
                "change": "major_change",
                "should_create_new_version": True,
                "changed_fields": ["direction", "reasoning"],
                "explanation": "The expected direction and thesis changed.",
            }

    service.llm = MockLLM()
    analysis = FakeAnalysisOutput(thesis_id="thesis-1", information_cutoff=datetime.utcnow())

    new_prediction = service.generate(analysis, existing_prediction=first)

    assert new_prediction.version == 2
    assert new_prediction.direction == PredictionDirection.DOWN
    assert first.status == PredictionStatus.SUPERSEDED
    assert len(service.predictions) == 2
    assert service.llm.calls == 2

