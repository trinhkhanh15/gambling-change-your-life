from uuid import uuid4

from application.ports.repository import Repository
from domain.models.evaluation import Evaluation
from domain.models.prediction import Direction, Prediction, PredictionStatus
from domain.models.reality import Reality


class EvaluationLayer:
    def __init__(self, repository: Repository, *, magnitude_tolerance: float = 0.10):
        if magnitude_tolerance <= 0:
            raise ValueError("magnitude_tolerance must be positive")
        self._repository = repository
        self._magnitude_tolerance = magnitude_tolerance

    def evaluate(self, prediction: Prediction, reality: Reality) -> Evaluation:
        if prediction.status != PredictionStatus.ACTIVE:
            raise ValueError("only active predictions can be evaluated")
        if reality.prediction_id != prediction.id:
            raise ValueError("reality.prediction_id does not match prediction.id")
        if reality.target != prediction.target or reality.metric not in prediction.metrics:
            raise ValueError("reality target and metric must match the prediction")
        if reality.baseline != prediction.baseline:
            raise ValueError("reality baseline must match the prediction baseline")
        if reality.observed_at.date() < prediction.horizon_end:
            raise ValueError("reality cannot resolve a prediction before its horizon ends")

        direction_score = self._direction_score(prediction.direction, reality.actual_direction)
        magnitude_score = max(
            0.0,
            1.0 - abs(prediction.expected_change_pct - reality.actual_change_pct) / self._magnitude_tolerance,
        )
        reason_score = self._jaccard(prediction.predicted_drivers, reality.actual_drivers)
        weights = [(direction_score, 0.4), (magnitude_score, 0.4)]
        if reason_score is not None:
            weights.append((reason_score, 0.2))
        total_weight = sum(weight for _, weight in weights)
        matching_score = sum(score * weight for score, weight in weights) / total_weight

        evaluation = Evaluation(
            id=f"evaluation-{uuid4().hex[:12]}",
            prediction_id=prediction.id,
            prediction_version=prediction.version,
            reality_id=reality.id,
            direction_score=direction_score,
            magnitude_score=magnitude_score,
            reason_score=reason_score,
            matching_score=matching_score,
            explanation=(
                f"Direction={direction_score:.2f}, magnitude={magnitude_score:.2f}, "
                f"drivers={reason_score if reason_score is not None else 'not assessed'}."
            ),
        )
        self._repository.save_many(
            [
                reality,
                evaluation,
                prediction.model_copy(update={"status": PredictionStatus.RESOLVED}),
            ]
        )
        return evaluation

    @staticmethod
    def _direction_score(predicted: Direction, actual: Direction) -> float:
        if predicted == actual:
            return 1.0
        if Direction.FLAT in (predicted, actual):
            return 0.5
        return 0.0

    @staticmethod
    def _jaccard(predicted: list[str], actual: list[str]) -> float | None:
        if not actual:
            return None
        left = {item.strip().lower() for item in predicted if item.strip()}
        right = {item.strip().lower() for item in actual if item.strip()}
        union = left | right
        return len(left & right) / len(union) if union else 0.0
