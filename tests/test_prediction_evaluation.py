from datetime import date, datetime, timezone

import pytest

from domain.models.analyse_layer import AnalyseOutput
from domain.models.feedback import (
    Evaluation,
    Evaluation_LLMOutput,
    Reality,
    Direction,
)
from domain.models.prediction import (
    Prediction,
    PredictionChange,
    PredictionDirection,
    PredictionLLMOutput,
    PredictionComparisonLLMOutput,
    PredictionStatus,
)
from service.pipelines.prediction_service import PredictionService
from service.pipelines.evaluation_service import (
    EvaluationService,
    calculate_matching_score,
)


class MockLLM:
    """
    Mock LLM used to test PredictionService and EvaluationService
    without calling a real LLM/API.
    """

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def generate_response(self, system_prompt, response_model):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "response_model": response_model,
            }
        )

        response = self.responses.pop(0)

        if isinstance(response, response_model):
            return response

        return response_model.model_validate(response)


def make_analysis_output(
    thesis_id: str = "thesis-1",
) -> AnalyseOutput:
    return AnalyseOutput(
        thesis_id=thesis_id,
        prediction="Revenue is expected to increase.",
        evidence=["Revenue growth has remained positive."],
        counter_evidence=["Macroeconomic uncertainty remains."],
        confidence=0.8,
    )


def make_prediction_llm_output(
    direction=PredictionDirection.UP,
    confidence=0.8,
    reasoning="Revenue is expected to increase because demand is improving.",
):
    return PredictionLLMOutput(
        target="Spotify",
        metrics=["revenue"],
        direction=direction,
        horizon_start=date(2026, 10, 1),
        horizon_end=date(2026, 12, 31),
        baseline=100.0,
        reasoning=reasoning,
        predicted_drivers=[
            "subscriber growth",
            "pricing",
        ],
        confidence=confidence,
        resolution_criteria=[
            "Revenue increases during the prediction horizon."
        ],
    )


def make_reality(
    direction=Direction.UP,
    actual_value=110.0,
):
    return Reality(
        target="Spotify",
        metric="revenue",
        actual_value=actual_value,
        actual_direction=direction,
        observed_at=datetime.now(timezone.utc),
        source="test",
        reasoning="Revenue increased because subscriber growth continued.",
        evidence=["Revenue increased during the observed period."],
        actual_drivers=["subscriber growth"],
    )


# ============================================================
# PredictionService tests
# ============================================================


def test_generate_new_prediction():
    llm = MockLLM(
        [
            make_prediction_llm_output(),
        ]
    )

    service = PredictionService(llm_client=llm)

    prediction = service.generate(
        analysis_output=make_analysis_output(),
    )

    assert isinstance(prediction, Prediction)

    assert prediction.id == "pred-1"
    assert prediction.thesis_id == "thesis-1"
    assert prediction.version == 1

    assert prediction.target == "Spotify"
    assert prediction.direction == PredictionDirection.UP
    assert prediction.status == PredictionStatus.ACTIVE

    assert len(service.get_predictions()) == 1
    assert service.get_predictions()[0] == prediction

    assert len(llm.calls) == 1
    assert llm.calls[0]["response_model"] is PredictionLLMOutput


def test_update_prediction_without_major_change_keeps_existing_prediction():
    old_prediction_output = make_prediction_llm_output()

    comparison_output = PredictionComparisonLLMOutput(
        change=PredictionChange.NO_CHANGE,
        should_create_new_version=False,
        changed_fields=[],
        explanation="The new prediction has the same core meaning.",
    )

    llm = MockLLM(
        [
            old_prediction_output,      # generate() lần đầu
            old_prediction_output,      # update() tạo prediction mới
            comparison_output,          # update() compare old vs new
        ]
    )

    service = PredictionService(llm_client=llm)

    old_prediction = service.generate(
        analysis_output=make_analysis_output(),
    )

    result = service.update(
        existing_prediction=old_prediction,
        analysis_output=make_analysis_output(),
    )

    assert result is old_prediction

    assert result.version == 1
    assert result.status == PredictionStatus.ACTIVE

    # No new prediction should have been persisted.
    assert len(service.get_predictions()) == 1
    assert service.get_predictions()[0] is old_prediction


def test_update_prediction_with_major_change_creates_new_version():
    first_prediction_output = make_prediction_llm_output(
        direction=PredictionDirection.UP,
        confidence=0.8,
        reasoning="Revenue is expected to increase because demand is improving.",
    )

    second_prediction_output = make_prediction_llm_output(
        direction=PredictionDirection.DOWN,
        confidence=0.7,
        reasoning="Revenue is expected to decrease because demand is weakening.",
    )

    comparison_output = PredictionComparisonLLMOutput(
        change=PredictionChange.MAJOR_CHANGE,
        should_create_new_version=True,
        changed_fields=[
            "direction",
            "reasoning",
        ],
        explanation="The expected direction and core reasoning changed.",
    )

    llm = MockLLM(
        [
            first_prediction_output,
            second_prediction_output,
            comparison_output,
        ]
    )

    service = PredictionService(llm_client=llm)

    old_prediction = service.generate(
        analysis_output=make_analysis_output(),
    )

    new_prediction = service.update(
        existing_prediction=old_prediction,
        analysis_output=make_analysis_output(),
    )

    assert new_prediction is not old_prediction

    assert old_prediction.version == 1
    assert old_prediction.status == PredictionStatus.SUPERSEDED

    assert new_prediction.version == 2
    assert new_prediction.status == PredictionStatus.ACTIVE

    assert new_prediction.thesis_id == old_prediction.thesis_id

    assert len(service.get_predictions()) == 2


def test_minor_change_with_true_new_version_flag_exposes_inconsistent_llm_output():
    """
    This test documents a potential production logic problem.

    The prompt says:
        should_create_new_version = true ONLY when change = major_change

    But PredictionService currently trusts the boolean directly.

    Therefore this test is expected to FAIL if the service is changed
    to enforce the prompt invariant, and PASS with the current
    implementation.

    It is intentionally written as a specification check.
    """

    first_prediction_output = make_prediction_llm_output()

    second_prediction_output = make_prediction_llm_output(
        confidence=0.81,
        reasoning="Revenue is expected to increase because demand continues improving.",
    )

    inconsistent_comparison = PredictionComparisonLLMOutput(
        change=PredictionChange.MINOR_CHANGE,
        should_create_new_version=True,
        changed_fields=["confidence"],
        explanation="Only a minor confidence change occurred.",
    )

    llm = MockLLM(
        [
            first_prediction_output,
            second_prediction_output,
            inconsistent_comparison,
        ]
    )

    service = PredictionService(llm_client=llm)

    old_prediction = service.generate(
        analysis_output=make_analysis_output(),
    )

    result = service.update(
        existing_prediction=old_prediction,
        analysis_output=make_analysis_output(),
    )

    # According to compare_prediction.txt, this should remain
    # the same prediction because change != major_change.
    assert result is old_prediction
    assert result.version == 1
    assert len(service.get_predictions()) == 1


# ============================================================
# EvaluationService tests
# ============================================================


def test_calculate_matching_score_with_all_dimensions():
    score = calculate_matching_score(
        direction_score=1.0,
        magnitude_score=0.5,
        reason_score=1.0,
    )

    expected = (
        1.0 * 0.4
        + 0.5 * 0.4
        + 1.0 * 0.2
    )

    assert score == pytest.approx(expected)


def test_calculate_matching_score_without_reason_score():
    score = calculate_matching_score(
        direction_score=1.0,
        magnitude_score=0.5,
        reason_score=None,
    )

    expected = (
        1.0 * 0.4 / 0.8
        + 0.5 * 0.4 / 0.8
    )

    assert score == pytest.approx(expected)


def test_evaluate_prediction_against_reality():
    llm = MockLLM(
        [
            Evaluation_LLMOutput(
                direction_score=1.0,
                magnitude_score=0.5,
                reason_score=1.0,
            )
        ]
    )

    service = EvaluationService(llm_client=llm)

    prediction = Prediction(
        id="pred-1",
        thesis_id="thesis-1",
        version=1,
        target="Spotify",
        metrics=["revenue"],
        direction=PredictionDirection.UP,
        horizon_start=date(2026, 10, 1),
        horizon_end=date(2026, 12, 31),
        baseline=100.0,
        reasoning="Revenue is expected to increase.",
        predicted_drivers=["subscriber growth"],
        confidence=0.8,
        resolution_criteria=[
            "Revenue increases."
        ],
        status=PredictionStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        information_cutoff=datetime.now(timezone.utc),
    )

    reality = make_reality(
        direction=Direction.UP,
        actual_value=110.0,
    )

    evaluation = service.evaluate(
        prediction=prediction,
        reality=reality,
    )

    assert isinstance(evaluation, Evaluation)

    assert evaluation.prediction_id == prediction.id
    assert evaluation.prediction_version == prediction.version

    assert evaluation.actual_value == reality.actual_value
    assert evaluation.actual_direction == reality.actual_direction

    assert evaluation.direction_score == 1.0
    assert evaluation.magnitude_score == 0.5
    assert evaluation.reason_score == 1.0

    expected_score = (
        1.0 * 0.4
        + 0.5 * 0.4
        + 1.0 * 0.2
    )

    assert evaluation.matching_score == pytest.approx(expected_score)

    assert evaluation.actual_drivers == reality.actual_drivers
    assert evaluation.reasoning == reality.reasoning

    assert len(llm.calls) == 1
    assert llm.calls[0]["response_model"] is Evaluation_LLMOutput


def test_evaluate_rejects_invalid_prediction():
    llm = MockLLM([])

    service = EvaluationService(llm_client=llm)

    reality = make_reality()

    with pytest.raises(Exception):
        service.evaluate(
            prediction="not a prediction",
            reality=reality,
        )


def test_evaluate_rejects_invalid_reality():
    llm = MockLLM([])

    service = EvaluationService(llm_client=llm)

    prediction = Prediction(
        id="pred-1",
        thesis_id="thesis-1",
        version=1,
        target="Spotify",
        metrics=["revenue"],
        direction=PredictionDirection.UP,
        horizon_start=date(2026, 10, 1),
        horizon_end=date(2026, 12, 31),
        baseline=100.0,
        reasoning="Revenue is expected to increase.",
        predicted_drivers=["subscriber growth"],
        confidence=0.8,
        resolution_criteria=["Revenue increases."],
        status=PredictionStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        information_cutoff=datetime.now(timezone.utc),
    )

    with pytest.raises(Exception):
        service.evaluate(
            prediction=prediction,
            reality="not reality",
        )