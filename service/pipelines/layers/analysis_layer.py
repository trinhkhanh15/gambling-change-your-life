import json
from uuid import uuid4

from application.ports.llm import LLMClient
from application.ports.repository import Repository
from domain.models.evaluation import Evaluation
from domain.models.event import Event, Evidence
from domain.models.prediction import Prediction
from domain.models.reality import Reality
from domain.models.routing import RouterAction, RouterDecision, ThesisUpdateDraft
from domain.models.thesis import Thesis, ThesisDraft, ThesisStatus


class AnalysisLayer:
    def __init__(self, llm: LLMClient, repository: Repository):
        self._llm = llm
        self._repository = repository

    def generate_thesis(self, event: Event, recent_feedback: list[dict] | None = None) -> Thesis:
        prompt = "Generate a falsifiable business thesis from this event.\nCONTEXT_JSON\n" + json.dumps(
            {
                "event": event.model_dump(mode="json"),
                "recent_resolved_feedback": recent_feedback or [],
            },
            ensure_ascii=False,
        )
        draft = ThesisDraft.model_validate(
            self._llm.generate_response(system_prompt=prompt, response_model=ThesisDraft)
        )
        now = event.published_at
        thesis = Thesis(
            id=f"thesis-{uuid4().hex[:12]}",
            ticker=draft.ticker,
            core_claim=draft.core_claim,
            core_assumptions=draft.core_assumptions,
            status=ThesisStatus.ACTIVE,
            strength=draft.initial_strength,
            evidence=[Evidence(event_id=event.id, timestamp=event.published_at, point=point) for point in draft.evidence_points],
            counter_evidence=[Evidence(event_id=event.id, timestamp=event.published_at, point=point) for point in draft.counter_evidence_points],
            reasoning=draft.reasoning,
            created_at=now,
            updated_at=now,
        )
        return self._repository.save(thesis)

    def process_event(self, event: Event) -> tuple[RouterDecision, Thesis | None]:
        recent_feedback = self._recent_feedback(as_of=event.published_at)
        active_theses = [
            thesis for thesis in self._repository.list(Thesis)
            if thesis.status == ThesisStatus.ACTIVE
        ]
        prompt = "Route this event against active theses.\nCONTEXT_JSON\n" + json.dumps(
            {
                "event": event.model_dump(mode="json"),
                "candidate_theses": [thesis.model_dump(mode="json") for thesis in active_theses],
                "recent_resolved_feedback": recent_feedback,
            },
            ensure_ascii=False,
        )
        decision = RouterDecision.model_validate(
            self._llm.generate_response(system_prompt=prompt, response_model=RouterDecision)
        )
        if decision.action == RouterAction.IGNORE:
            return decision, None
        if decision.action == RouterAction.GENERATE_THESIS:
            return decision, self.generate_thesis(event, recent_feedback)

        target = next((item for item in active_theses if item.id == decision.target_thesis_id), None)
        if target is None:
            raise ValueError(f"router selected unknown or inactive thesis: {decision.target_thesis_id}")
        update_prompt = "Update thesis evidence and decide whether to kill it.\nCONTEXT_JSON\n" + json.dumps(
            {
                "event": event.model_dump(mode="json"),
                "thesis": target.model_dump(mode="json"),
                "recent_resolved_feedback": recent_feedback,
            },
            ensure_ascii=False,
        )
        draft = ThesisUpdateDraft.model_validate(
            self._llm.generate_response(system_prompt=update_prompt, response_model=ThesisUpdateDraft)
        )
        evidence = list(target.evidence) + [
            Evidence(event_id=event.id, timestamp=event.published_at, point=point)
            for point in draft.new_evidence_points
        ]
        counter_evidence = list(target.counter_evidence) + [
            Evidence(event_id=event.id, timestamp=event.published_at, point=point)
            for point in draft.new_counter_evidence_points
        ]
        updated_data = target.model_dump(mode="python")
        updated_data.update(
            {
                "status": draft.new_status,
                "strength": draft.new_strength,
                "evidence": evidence,
                "counter_evidence": counter_evidence,
                "reasoning": draft.updated_reasoning,
                "updated_at": event.published_at,
                "killed_at": event.published_at if draft.new_status == ThesisStatus.KILLED else None,
                "kill_reason": draft.kill_reason,
            }
        )
        updated = Thesis.model_validate(updated_data)
        return decision, self._repository.save(updated)

    def _recent_feedback(self, *, as_of, limit: int = 5) -> list[dict]:
        evaluations = self._repository.list(Evaluation)
        feedback = []
        for evaluation in reversed(evaluations):
            reality = self._repository.get(Reality, evaluation.reality_id)
            if reality is None or reality.observed_at >= as_of:
                continue
            prediction = self._repository.get(Prediction, evaluation.prediction_id)
            thesis = (
                self._repository.get(Thesis, prediction.thesis_id)
                if prediction is not None
                else None
            )
            feedback.append(
                {
                    "ticker": thesis.ticker if thesis is not None else None,
                    "prediction_id": evaluation.prediction_id,
                    "direction_score": evaluation.direction_score,
                    "magnitude_score": evaluation.magnitude_score,
                    "matching_score": evaluation.matching_score,
                    "explanation": evaluation.explanation,
                    "resolved_at": reality.observed_at.isoformat(),
                }
            )
            if len(feedback) == limit:
                break
        feedback.reverse()
        return feedback
