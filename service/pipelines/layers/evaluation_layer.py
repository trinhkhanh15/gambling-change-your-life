from uuid import uuid4

from application.ports.llm import LLMClient
from application.ports.repository import Repository
from domain.models.evaluation import Evaluation, EvaluationDraft
from domain.models.prediction import Prediction, PredictionStatus
from domain.models.reality import Reality
from domain.prompts import render_prompt


class EvaluationLayer:
    def __init__(self, llm: LLMClient, repository: Repository):
        self._llm = llm
        self._repository = repository

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

        prompt = render_prompt(
            "evaluate",
            {
                "prediction": prediction.model_dump(mode="json"),
                "reality": reality.model_dump(mode="json"),
                "actual_change_pct": reality.actual_change_pct,
            },
        )
        draft = EvaluationDraft.model_validate(
            self._llm.generate_response(system_prompt=prompt, response_model=EvaluationDraft)
        )
        direction_score, magnitude_score = draft.direction_score, draft.magnitude_score
        # No actual drivers means the reasoning cannot be assessed, whatever the LLM returned.
        reason_score = draft.reason_score if reality.actual_drivers else None
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
            explanation=draft.explanation,
        )
        self._repository.save_many(
            [
                reality,
                evaluation,
                prediction.model_copy(update={"status": PredictionStatus.RESOLVED}),
            ]
        )
        return evaluation
