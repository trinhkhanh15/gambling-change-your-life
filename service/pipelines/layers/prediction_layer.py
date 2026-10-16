from datetime import datetime, timezone
from uuid import uuid4

from application.ports.llm import LLMClient
from application.ports.repository import Repository
from domain.models.prediction import (
    Prediction,
    PredictionChange,
    PredictionComparison,
    PredictionDraft,
    PredictionStatus,
)
from domain.models.thesis import Thesis, ThesisStatus
from domain.prompts import render_prompt


class PredictionLayer:
    def __init__(self, llm: LLMClient, repository: Repository):
        self._llm = llm
        self._repository = repository

    def generate(
        self,
        thesis: Thesis,
        *,
        market_context: dict | None = None,
        information_cutoff: datetime | None = None,
    ) -> Prediction:
        if thesis.status != ThesisStatus.ACTIVE:
            raise ValueError("predictions can only be generated for active theses")
        history = [p for p in self._repository.list(Prediction) if p.thesis_id == thesis.id]
        active = [p for p in history if p.status == PredictionStatus.ACTIVE]
        if len(active) > 1:
            raise ValueError(f"thesis {thesis.id} has multiple active predictions")

        prompt = render_prompt(
            "prediction",
            {
                "thesis": thesis.model_dump(mode="json"),
                "existing_prediction": active[0].model_dump(mode="json") if active else None,
            },
        )
        draft = PredictionDraft.model_validate(
            self._llm.generate_response(system_prompt=prompt, response_model=PredictionDraft)
        )
        draft_fields = draft.model_dump()
        if abs(draft_fields.get("expected_change_pct", 0.0)) >= 1.0:
            draft_fields["expected_change_pct"] = draft_fields["expected_change_pct"] / 100.0
        if market_context:
            draft_fields.update(market_context)
        version = max((p.version for p in history), default=0) + 1
        prediction = Prediction(
            id=f"prediction-{uuid4().hex[:12]}",
            thesis_id=thesis.id,
            version=version,
            **draft_fields,
            information_cutoff=information_cutoff or datetime.now(timezone.utc),
        )
        if active:
            if not self._is_major_change(active[0], prediction):
                return active[0]  # same prediction in different words: keep the current version
            self._repository.save(active[0].model_copy(update={"status": PredictionStatus.SUPERSEDED}))
        return self._repository.save(prediction)

    def _is_major_change(self, old: Prediction, new: Prediction) -> bool:
        prompt = render_prompt(
            "compare_prediction",
            {"old_prediction": old.model_dump(mode="json"), "new_prediction": new.model_dump(mode="json")},
        )
        comparison = PredictionComparison.model_validate(
            self._llm.generate_response(system_prompt=prompt, response_model=PredictionComparison)
        )
        return comparison.change == PredictionChange.MAJOR_CHANGE

    def invalidate_for_thesis(self, thesis_id: str) -> list[Prediction]:
        invalidated = []
        for prediction in self._repository.list(Prediction):
            if prediction.thesis_id == thesis_id and prediction.status == PredictionStatus.ACTIVE:
                updated = prediction.model_copy(update={"status": PredictionStatus.INVALIDATED})
                invalidated.append(self._repository.save(updated))
        return invalidated
