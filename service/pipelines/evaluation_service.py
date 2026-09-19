from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

from domain.exceptions import EvaluationValidationError, RealityValidationError
from domain.models.feedback import Evaluation, Reality
from domain.models.prediction import Prediction, PredictionDirection

DEFAULT_MAGNITUDE_TOLERANCE = 0.20
DIRECTION_WEIGHT = 0.4
MAGNITUDE_WEIGHT = 0.4
REASON_WEIGHT = 0.2


def _normalize_direction(value: str | PredictionDirection) -> str:
    if isinstance(value, PredictionDirection):
        return value.value
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in {"UP", "DOWN", "FLAT"}:
            return normalized
    raise ValueError("direction must be one of: UP, DOWN, FLAT")


def _normalize_driver_list(drivers: Sequence[str] | None) -> set[str]:
    if not drivers:
        return set()
    return {d.strip().lower().replace("-", " ").replace("_", " ") for d in drivers if str(d).strip()}


def calculate_direction_score(predicted_direction: str | PredictionDirection, actual_direction: str | PredictionDirection) -> float:
    predicted = _normalize_direction(predicted_direction)
    actual = _normalize_direction(actual_direction)

    if predicted == actual:
        return 1.0
    if predicted == PredictionDirection.UP.value and actual == PredictionDirection.FLAT.value:
        return 0.5
    if predicted == PredictionDirection.DOWN.value and actual == PredictionDirection.FLAT.value:
        return 0.5
    if predicted == PredictionDirection.UP.value and actual == PredictionDirection.DOWN.value:
        return 0.0
    if predicted == PredictionDirection.DOWN.value and actual == PredictionDirection.UP.value:
        return 0.0
    return 0.5 if predicted == actual else 0.0


def calculate_magnitude_score(predicted_value: float, actual_value: float, tolerance: float = DEFAULT_MAGNITUDE_TOLERANCE) -> float:
    if tolerance <= 0:
        raise ValueError("tolerance must be greater than zero")
    error = abs(float(predicted_value) - float(actual_value))
    magnitude = max(0.0, 1.0 - (error / tolerance))
    return max(0.0, min(1.0, magnitude))


def calculate_reason_score(predicted_drivers: Sequence[str] | None, actual_drivers: Sequence[str] | None) -> float | None:
    if actual_drivers is None:
        return None

    predicted = _normalize_driver_list(predicted_drivers)
    actual = _normalize_driver_list(actual_drivers)
    if not actual:
        return None
    if not predicted and not actual:
        return None

    union = predicted | actual
    if not union:
        return None
    intersection = predicted & actual
    return len(intersection) / len(union)


def calculate_matching_score(
    direction_score: float,
    magnitude_score: float,
    reason_score: float | None,
    direction_weight: float = DIRECTION_WEIGHT,
    magnitude_weight: float = MAGNITUDE_WEIGHT,
    reason_weight: float = REASON_WEIGHT,
) -> float:
    if not 0.0 <= direction_score <= 1.0:
        raise ValueError("direction_score must be between 0 and 1")
    if not 0.0 <= magnitude_score <= 1.0:
        raise ValueError("magnitude_score must be between 0 and 1")
    if reason_score is not None and not 0.0 <= reason_score <= 1.0:
        raise ValueError("reason_score must be between 0 and 1 or None")
    if direction_weight <= 0 or magnitude_weight <= 0:
        raise ValueError("weights must be positive")

    if reason_score is None:
        total_weight = direction_weight + magnitude_weight
        if total_weight <= 0:
            raise ValueError("weights must sum to a positive number")
        score = 100.0 * (direction_score ** (direction_weight / total_weight)) * (magnitude_score ** (magnitude_weight / total_weight))
        return max(0.0, min(100.0, score))

    total_weight = direction_weight + magnitude_weight + reason_weight
    score = 100.0 * (direction_score ** (direction_weight / total_weight)) * (magnitude_score ** (magnitude_weight / total_weight)) * (reason_score ** (reason_weight / total_weight))
    return max(0.0, min(100.0, score))


class EvaluationService:
    def evaluate(self, prediction: Prediction, reality: Reality) -> Evaluation:
        if not isinstance(prediction, Prediction):
            raise EvaluationValidationError("prediction must be a valid Prediction model")
        if not isinstance(reality, Reality):
            raise RealityValidationError("reality must be a valid Reality model")

        direction = calculate_direction_score(prediction.direction, reality.actual_direction)
        magnitude = calculate_magnitude_score(prediction.predicted_value, reality.actual_value)
        reason_score = calculate_reason_score(prediction.predicted_drivers, reality.actual_drivers)
        matching_score = calculate_matching_score(direction, magnitude, reason_score)

        return Evaluation(
            prediction_id=prediction.id,
            prediction_version=prediction.version,
            actual_value=reality.actual_value,
            actual_direction=reality.actual_direction,
            direction_score=direction,
            magnitude_score=magnitude,
            reason_score=reason_score,
            matching_score=matching_score,
            reasoning=reality.reasoning,
            actual_drivers=reality.actual_drivers,
            evaluated_at=datetime.utcnow(),
        )
