from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from domain.exceptions import AnalysisOutputError, LLMGenerationError
from domain.models.prediction import Prediction, PredictionLLMOutput, PredictionStatus
from service.shared.prompt_renderer import PromptRenderer


class PredictionService:
    def __init__(self, llm_client: Any | None = None, prompt_renderer: PromptRenderer | None = None):
        self.llm = llm_client
        self.prompt_renderer = prompt_renderer or PromptRenderer()
        self.predictions: list[Prediction] = []

    def _build_llm_context(self, analysis_output: Any, existing_prediction: Prediction | None = None) -> str:
        payload: dict[str, Any] = {"analysis_output": analysis_output}
        if existing_prediction is not None:
            payload["existing_prediction"] = existing_prediction.model_dump(mode="json")
        return json.dumps(payload, default=str)

    @staticmethod
    def _serialize_analysis(analysis_output: Any) -> str:
        if hasattr(analysis_output, "model_dump"):
            return json.dumps(analysis_output.model_dump(), default=str)
        return json.dumps(analysis_output.__dict__, default=str)

    def _get_llm_response(self, analysis_output: Any, existing_prediction: Prediction | None = None) -> PredictionLLMOutput:
        if self.llm is None:
            raise LLMGenerationError("No LLM client configured for prediction generation")

        prompt = self.prompt_renderer.prediction_prompt(
            analysis=self._build_llm_context(analysis_output, existing_prediction),
            thesis_context=self._serialize_analysis(analysis_output),
        )
        raw_response = self.llm.generate_response(
            system_prompt=prompt,
            response_model=PredictionLLMOutput,
        )

        if isinstance(raw_response, str):
            try:
                return PredictionLLMOutput.model_validate(json.loads(raw_response))
            except json.JSONDecodeError as exc:
                raise LLMGenerationError("LLM returned invalid JSON for prediction generation") from exc

        if isinstance(raw_response, dict):
            return PredictionLLMOutput.model_validate(raw_response)

        if hasattr(raw_response, "model_dump"):
            return PredictionLLMOutput.model_validate(raw_response.model_dump())

        raise LLMGenerationError("LLM response does not match the expected structured prediction schema")

    def _persist_prediction(self, prediction: Prediction) -> Prediction:
        if prediction.status == PredictionStatus.ACTIVE:
            for previous in self.predictions:
                if previous.thesis_id == prediction.thesis_id and previous.id != prediction.id and previous.status == PredictionStatus.ACTIVE:
                    previous.status = PredictionStatus.SUPERSEDED
        self.predictions.append(prediction)
        return prediction

    def _should_create_new_version(self, existing_prediction: Prediction | None, llm_output: PredictionLLMOutput) -> bool:
        if existing_prediction is None:
            return True

        fields = [
            llm_output.target,
            llm_output.metrics,
            llm_output.direction.value,
            llm_output.horizon_start,
            llm_output.horizon_end,
            llm_output.baseline,
            llm_output.reasoning,
            llm_output.predicted_drivers,
            llm_output.confidence,
            llm_output.resolution_criteria,
        ]
        current_fields = [
            existing_prediction.target,
            existing_prediction.metrics,
            existing_prediction.direction.value,
            existing_prediction.horizon_start,
            existing_prediction.horizon_end,
            existing_prediction.baseline,
            existing_prediction.reasoning,
            existing_prediction.predicted_drivers,
            existing_prediction.confidence,
            existing_prediction.resolution_criteria,
        ]
        return fields != current_fields

    def generate(self, analysis_output: Any, existing_prediction: Prediction | None = None) -> Prediction:
        if analysis_output is None:
            raise AnalysisOutputError("analysis_output is required")
        if getattr(analysis_output, "thesis_id", None) is None:
            raise AnalysisOutputError("Analysis output must include a thesis_id")

        try:
            llm_output = self._get_llm_response(analysis_output, existing_prediction)
        except (TypeError, ValueError, AttributeError) as exc:
            raise AnalysisOutputError("Invalid analysis output for prediction generation") from exc

        payload = {
            "id": f"pred-{len(self.predictions) + 1}",
            "thesis_id": str(analysis_output.thesis_id),
            "version": 1 if existing_prediction is None else existing_prediction.version + 1,
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
            "status": PredictionStatus.ACTIVE.value,
            "created_at": datetime.utcnow(),
            "information_cutoff": getattr(analysis_output, "information_cutoff", datetime.utcnow()),
        }

        prediction = Prediction.model_validate(payload)

        if existing_prediction is not None and not self._should_create_new_version(existing_prediction, llm_output):
            existing_prediction.status = PredictionStatus.ACTIVE
            return existing_prediction

        if existing_prediction is not None:
            existing_prediction.status = PredictionStatus.SUPERSEDED

        return self._persist_prediction(prediction)

    def update(self, existing_prediction: Prediction, analysis_output: Any) -> Prediction:
        return self.generate(analysis_output=analysis_output, existing_prediction=existing_prediction)

    def generate_prediction(self, prediction: Prediction) -> Prediction:
        return self._persist_prediction(prediction)

    def get_predictions(self) -> list[Prediction]:
        return list(self.predictions)