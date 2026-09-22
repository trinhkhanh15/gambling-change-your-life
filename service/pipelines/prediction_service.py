
from __future__ import annotations

import json
from datetime import datetime, timezone
from domain.models.analyse_layer import AnalyseOutput, Thesis

from infra.llm.openai import OpenAIClient

from domain.exceptions import AnalysisOutputError, LLMGenerationError
from domain.models.prediction import (
    Prediction,
    PredictionComparisonLLMOutput,
    PredictionLLMOutput,
    PredictionStatus,
    PredictionChange
)
from service.shared.prompt_renderer import PromptRenderer


class PredictionService:
    def __init__(
        self,
        llm_client: OpenAIClient | None = None,
        prompt_renderer: PromptRenderer | None = None,
    ):
        self.llm = llm_client
        self.prompt_renderer = prompt_renderer or PromptRenderer()
        self.predictions: list[Prediction] = []

    @staticmethod
    def _serialize(data: AnalyseOutput | Thesis | Prediction) -> str:
        """Serialize Pydantic models or regular objects to JSON."""
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        elif hasattr(data, "__dict__"):
            data = data.__dict__

        return json.dumps(data, default=str)

    def _get_llm_response(
        self,
        analysis_output: AnalyseOutput,
        existing_prediction: Prediction | None = None,
    ) -> PredictionLLMOutput:

        if self.llm is None:
            raise LLMGenerationError(
                "No LLM client configured for prediction generation"
            )

        existing_prediction_json = (
            self._serialize(existing_prediction)
            if existing_prediction is not None
            else None
        )

        prompt = self.prompt_renderer.prediction_prompt(
            analysis=self._serialize(analysis_output),
            existing_prediction=existing_prediction_json,
        )

        response = self.llm.generate_response(
            system_prompt=prompt,
            response_model=PredictionLLMOutput,
        )

        return PredictionLLMOutput.model_validate(response)

    def _compare_predictions(
        self,
        old_prediction: Prediction,
        new_prediction: Prediction,
    ) -> PredictionComparisonLLMOutput:
        if self.llm is None:
            raise LLMGenerationError(
                "No LLM client configured for prediction comparison"
            )

        prompt = self.prompt_renderer.compare_prediction_prompt(
            old_prediction=self._serialize(old_prediction),
            new_prediction=self._serialize(new_prediction),
        )

        response = self.llm.generate_response(
            system_prompt=prompt,
            response_model=PredictionComparisonLLMOutput,
        )

        return PredictionComparisonLLMOutput.model_validate(response)

    @staticmethod
    def _should_create_new_version(
        comparison: PredictionComparisonLLMOutput,
    ) -> bool:
        return comparison.should_create_new_version and comparison.change == PredictionChange.MAJOR_CHANGE

    def _build_prediction(
        self,
        analysis_output: AnalyseOutput,
        llm_output: PredictionLLMOutput,
        existing_prediction: Prediction | None,
    ) -> Prediction:
        now = datetime.now(timezone.utc)

        payload = {
            "id": f"pred-{len(self.predictions) + 1}",
            "thesis_id": str(analysis_output.thesis_id),
            "version": (
                1
                if existing_prediction is None
                else existing_prediction.version + 1
            ),
            "target": llm_output.target,
            "metrics": llm_output.metrics,
            "direction": llm_output.direction,
            "horizon_start": llm_output.horizon_start,
            "horizon_end": llm_output.horizon_end,
            "baseline": llm_output.baseline,
            "reasoning": llm_output.reasoning,
            "predicted_drivers": llm_output.predicted_drivers,
            "confidence": llm_output.confidence,
            "resolution_criteria": llm_output.resolution_criteria,
            "status": PredictionStatus.ACTIVE,
            "created_at": now,
            "information_cutoff": getattr(
                analysis_output,
                "information_cutoff",
                now,
            ),
        }

        return Prediction.model_validate(payload)

    def _persist_prediction(
        self,
        prediction: Prediction,
    ) -> Prediction:
        if prediction.status == PredictionStatus.ACTIVE:
            self._supersede_active_prediction(prediction)

        self.predictions.append(prediction)
        return prediction

    def _supersede_active_prediction(
        self,
        prediction: Prediction,
    ) -> None:
        for previous in self.predictions:
            if (
                previous.thesis_id == prediction.thesis_id
                and previous.id != prediction.id
                and previous.status == PredictionStatus.ACTIVE
            ):
                previous.status = PredictionStatus.SUPERSEDED

    def generate(
        self,
        analysis_output: AnalyseOutput,
        existing_prediction: Prediction | None = None,
    ) -> Prediction:
        self._validate_analysis_output(analysis_output)

        try:
            llm_output = self._get_llm_response(
                analysis_output=analysis_output,
                existing_prediction=existing_prediction,
            )
        except (TypeError, ValueError, AttributeError) as exc:
            raise AnalysisOutputError(
                "Invalid analysis output for prediction generation"
            ) from exc

        prediction = self._build_prediction(
            analysis_output=analysis_output,
            llm_output=llm_output,
            existing_prediction=existing_prediction,
        )

        if existing_prediction is None:
            return self._persist_prediction(prediction)

        comparison = self._compare_predictions(
            old_prediction=existing_prediction,
            new_prediction=prediction,
        )

        if not self._should_create_new_version(comparison):
            existing_prediction.status = PredictionStatus.ACTIVE
            return existing_prediction

        existing_prediction.status = PredictionStatus.SUPERSEDED

        return self._persist_prediction(prediction)

    @staticmethod
    def _validate_analysis_output(
        analysis_output: AnalyseOutput,
    ) -> None:
        if analysis_output is None:
            raise AnalysisOutputError(
                "analysis_output is required"
            )

        if getattr(analysis_output, "thesis_id", None) is None:
            raise AnalysisOutputError(
                "Analysis output must include a thesis_id"
            )

    def update(
        self,
        existing_prediction: Prediction,
        analysis_output: AnalyseOutput,
    ) -> Prediction:
        return self.generate(
            analysis_output=analysis_output,
            existing_prediction=existing_prediction,
        )

    def get_predictions(self) -> list[Prediction]:
        return list(self.predictions)

