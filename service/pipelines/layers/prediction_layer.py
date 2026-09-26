import json
from datetime import datetime, timezone
from uuid import uuid4

from application.ports.llm import LLMClient
from application.ports.repository import Repository
from domain.models.prediction import Prediction, PredictionDraft, PredictionStatus
from domain.models.thesis import Thesis, ThesisStatus


class PredictionLayer:
    def __init__(self, llm: LLMClient, repository: Repository):
        self._llm = llm
        self._repository = repository

    def generate(self, thesis: Thesis) -> Prediction:
        if thesis.status != ThesisStatus.ACTIVE:
            raise ValueError("predictions can only be generated for active theses")
        history = [p for p in self._repository.list(Prediction) if p.thesis_id == thesis.id]
        active = [p for p in history if p.status == PredictionStatus.ACTIVE]
        if len(active) > 1:
            raise ValueError(f"thesis {thesis.id} has multiple active predictions")

        prompt = "Create a measurable prediction from this thesis.\nCONTEXT_JSON\n" + json.dumps(
            {"thesis": thesis.model_dump(mode="json")}, ensure_ascii=False
        )
        draft = PredictionDraft.model_validate(
            self._llm.generate_response(system_prompt=prompt, response_model=PredictionDraft)
        )
        version = max((p.version for p in history), default=0) + 1
        if active:
            old = active[0].model_copy(update={"status": PredictionStatus.SUPERSEDED})
            self._repository.save(old)

        prediction = Prediction(
            id=f"prediction-{uuid4().hex[:12]}",
            thesis_id=thesis.id,
            version=version,
            **draft.model_dump(),
            information_cutoff=datetime.now(timezone.utc),
        )
        return self._repository.save(prediction)

    def invalidate_for_thesis(self, thesis_id: str) -> list[Prediction]:
        invalidated = []
        for prediction in self._repository.list(Prediction):
            if prediction.thesis_id == thesis_id and prediction.status == PredictionStatus.ACTIVE:
                updated = prediction.model_copy(update={"status": PredictionStatus.INVALIDATED})
                invalidated.append(self._repository.save(updated))
        return invalidated
