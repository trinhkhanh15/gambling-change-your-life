from datetime import date, timedelta
import json
from typing import TypeVar

from pydantic import BaseModel

from domain.models.prediction import Direction, PredictionDraft
from domain.models.routing import RouterAction, RouterDecision, ThesisUpdateDraft
from domain.models.thesis import ThesisDraft, ThesisStatus

T = TypeVar("T", bound=BaseModel)


class MockLLMClient:
    """Deterministic structured-output adapter for local tests and demos."""

    def generate_response(self, *, system_prompt: str, response_model: type[T]) -> T:
        context = self._context(system_prompt)
        if response_model is ThesisDraft:
            event = context.get("event", {})
            companies = event.get("companies_mentioned", [])
            return response_model.model_validate(
                {
                    "ticker": companies[0] if companies else "UNKNOWN",
                    "core_claim": f"{event.get('title', 'The event')} has a material effect on the business outlook.",
                    "core_assumptions": [
                        "The reported development persists through the prediction horizon.",
                        "No offsetting change materially reverses the business impact.",
                    ],
                    "initial_strength": 0.7,
                    "evidence_points": [event.get("title", "Event evidence")],
                    "counter_evidence_points": ["The event may already be reflected in expectations."],
                    "reasoning": "This mock reasoning is deterministic and is not investment research.",
                }
            )
        if response_model is RouterDecision:
            event = context.get("event", {})
            text = f"{event.get('title', '')} {event.get('content', '')}".lower()
            theses = context.get("candidate_theses", [])
            if any(word in text for word in ("donation", "commencement", "ethics lab", "charity", "philanthropy")):
                return RouterDecision(
                    action=RouterAction.IGNORE,
                    reasoning="The event is not materially related to business performance.",
                )
            matches = [
                thesis for thesis in theses
                if thesis.get("ticker", "").lower() in {c.lower() for c in event.get("companies_mentioned", [])}
            ]
            if matches:
                return RouterDecision(
                    action=RouterAction.UPDATE_THESIS,
                    target_thesis_id=matches[0]["id"],
                    reasoning="The event is associated with an active thesis and should update its evidence.",
                )
            return RouterDecision(
                action=RouterAction.GENERATE_THESIS,
                reasoning="No active thesis matches the event's companies.",
            )
        if response_model is ThesisUpdateDraft:
            event = context.get("event", {})
            thesis = context.get("thesis", {})
            text = f"{event.get('title', '')} {event.get('content', '')}".lower()
            if any(word in text for word in ("halt", "freeze", "cancel", "shift to asic", "orders stop")):
                reason = "The event invalidates a stated core assumption."
                return ThesisUpdateDraft(
                    new_status=ThesisStatus.KILLED,
                    new_strength=0.0,
                    new_counter_evidence_points=[event.get("title", "Thesis invalidation")],
                    updated_reasoning=f"Thesis killed: {reason}",
                    kill_reason=reason,
                )
            if any(word in text for word in ("bottleneck", "delay", "shortage")):
                return ThesisUpdateDraft(
                    new_status=ThesisStatus.ACTIVE,
                    new_strength=max(0.0, round(thesis.get("strength", 0.7) - 0.15, 2)),
                    new_counter_evidence_points=[event.get("title", "New counter-evidence")],
                    updated_reasoning="The event adds a supply or execution risk to the thesis.",
                )
            return ThesisUpdateDraft(
                new_status=ThesisStatus.ACTIVE,
                new_strength=min(0.95, round(thesis.get("strength", 0.7) + 0.1, 2)),
                new_evidence_points=[event.get("title", "New evidence")],
                updated_reasoning="The event strengthens a core assumption of the thesis.",
            )
        if response_model is PredictionDraft:
            thesis = context.get("thesis", {})
            start = date.today()
            return response_model.model_validate(
                {
                    "target": thesis.get("ticker", "UNKNOWN"),
                    "metrics": ["price_return"],
                    "direction": Direction.UP,
                    "horizon_start": start,
                    "horizon_end": start + timedelta(days=7),
                    "baseline": 100.0,
                    "expected_change_pct": 0.05,
                    "predicted_drivers": ["demand", "guidance"],
                    "confidence": 0.65,
                    "resolution_criteria": ["Compare closing price at horizon end with baseline."],
                    "reasoning": "Mock prediction for contract and integration testing.",
                }
            )
        raise ValueError(f"MockLLMClient has no fixture for {response_model.__name__}")

    @staticmethod
    def _context(prompt: str) -> dict:
        marker = "CONTEXT_JSON\n"
        if marker not in prompt:
            return {}
        raw = prompt.split(marker, 1)[1]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
