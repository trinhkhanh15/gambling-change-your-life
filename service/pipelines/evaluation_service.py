from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from domain.exceptions import (
    EvaluationValidationError,
    RealityValidationError,
)
from domain.models.feedback import (
    Evaluation,
    Reality,
    Evaluation_LLMOutput,
)
from domain.models.prediction import Prediction
from domain.prompts import evaluation_prompt


DIRECTION_WEIGHT = 0.4
MAGNITUDE_WEIGHT = 0.4
REASON_WEIGHT = 0.2


class DirectionMatch(str, Enum):
    MATCH = "match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class MagnitudeMatch(str, Enum):
    CLOSE = "close"
    OFF = "off"
    VERY_OFF = "very_off"


class ReasonMatch(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"


def get_llm_response(
    llm_client: Any,
    prediction: Prediction,
    reality: Reality,
) -> Evaluation_LLMOutput:

    if llm_client is None:
        raise ValueError(
            "No LLM client configured for evaluation generation"
        )

    prompt = evaluation_prompt(
        prediction=json.dumps(
            prediction.model_dump(mode="json"),
            default=str,
        ),
        reality=json.dumps(
            reality.model_dump(mode="json"),
            default=str,
        ),
    )

    return llm_client.generate_response(
        system_prompt=prompt,
        response_model=Evaluation_LLMOutput,
    )


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
        raise ValueError(
            "reason_score must be between 0 and 1 or None"
        )

    if direction_weight <= 0 or magnitude_weight <= 0:
        raise ValueError("direction and magnitude weights must be positive")

    if reason_score is None:
        total_weight = direction_weight + magnitude_weight

        score = (
            direction_score ** (direction_weight / total_weight)
            * magnitude_score ** (magnitude_weight / total_weight)
        )

    else:
        if reason_weight <= 0:
            raise ValueError("reason_weight must be positive")

        total_weight = (
            direction_weight
            + magnitude_weight
            + reason_weight
        )

        score = (
            direction_score ** (direction_weight / total_weight)
            * magnitude_score ** (magnitude_weight / total_weight)
            * reason_score ** (reason_weight / total_weight)
        )

    return max(0.0, min(1.0, score))


class EvaluationService:

    def __init__(self, llm_client: Any):
        self.llm_client = llm_client

    def evaluate(
        self,
        prediction: Prediction,
        reality: Reality,
    ) -> Evaluation:

        if not isinstance(prediction, Prediction):
            raise EvaluationValidationError(
                "prediction must be a valid Prediction model"
            )

        if not isinstance(reality, Reality):
            raise RealityValidationError(
                "reality must be a valid Reality model"
            )

        llm_output = get_llm_response(
            self.llm_client,
            prediction,
            reality,
        )

        direction_score = llm_output.direction_score
        magnitude_score = llm_output.magnitude_score
        reason_score = llm_output.reason_score

        matching_score = calculate_matching_score(
            direction_score,
            magnitude_score,
            reason_score,
        )

        return Evaluation(
            prediction_id=prediction.id,
            prediction_version=prediction.version,
            actual_value=reality.actual_value,
            actual_direction=reality.actual_direction,
            direction_score=direction_score,
            magnitude_score=magnitude_score,
            reason_score=reason_score,
            matching_score=matching_score,
            reasoning=reality.reasoning,
            actual_drivers=reality.actual_drivers,
            evaluated_at=datetime.now(timezone.utc),
        )