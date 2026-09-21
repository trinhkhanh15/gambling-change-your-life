from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from domain.schema.event import Event
from domain.schema.router import (
    RouterAction,
    RouterDecision,
    ThesisGenerateOutput,
    ThesisUpdateOutput,
)
from domain.schema.thesis import EvidenceItem, Thesis, ThesisStatus
from infra.llm import get_llm_client
from service.shared.prompt_renderer import PromptRenderer


class AnalysisLayer:
    def __init__(
        self,
        llm_client: Any | None = None,
        prompt_renderer: PromptRenderer | None = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.prompt_renderer = prompt_renderer or PromptRenderer()
        self.theses: Dict[str, Thesis] = {}
        self.event_log: List[Dict[str, Any]] = []
        self._counter: int = 0

    def _generate_thesis_id(self, ticker: str) -> str:
        self._counter += 1
        return f"THESIS-{ticker.upper()}-{self._counter:03d}"

    def filter_candidates(self, event: Event, top_k: int = 5) -> List[Thesis]:
        candidates = []
        event_tickers = {t.upper() for t in event.companies_mentioned}
        event_text = f"{event.title} {event.content}".lower()

        for thesis in self.theses.values():
            if thesis.status != ThesisStatus.ACTIVE:
                continue

            if thesis.ticker.upper() in event_tickers:
                candidates.append(thesis)
                continue

            thesis_words = set(thesis.core_claim.lower().split())
            intersection = thesis_words.intersection(set(event_text.split()))
            if len(intersection) >= 3:
                candidates.append(thesis)

        return candidates[:top_k]

    def route(
        self,
        event: Event,
        candidate_theses: Optional[List[Thesis]] = None,
    ) -> RouterDecision:
        candidates = (
            candidate_theses
            if candidate_theses is not None
            else self.filter_candidates(event)
        )

        candidates_data = [
            {
                "id": t.id,
                "ticker": t.ticker,
                "core_claim": t.core_claim,
                "core_assumptions": t.core_assumptions,
                "strength": t.strength,
                "status": t.status.value,
            }
            for t in candidates
        ]
        candidates_json = json.dumps(candidates_data, indent=2, ensure_ascii=False)

        expectation_str = (
            f"Metric: {event.expectation_context.consensus_metric}, "
            f"Expected: {event.expectation_context.expected_value}, "
            f"Actual: {event.expectation_context.actual_value}, "
            f"Surprise: {event.expectation_context.surprise_direction}"
            if event.expectation_context
            else "None"
        )

        prompt = self.prompt_renderer.router_prompt(
            event_id=event.id,
            published_at=event.published_at.isoformat(),
            source=event.source,
            title=event.title,
            content=event.content,
            companies=", ".join(event.companies_mentioned) or "None",
            sectors=", ".join(event.sectors) or "None",
            nature=event.nature.value,
            scope=event.scope.value,
            expectation_context=expectation_str,
            candidate_theses_json=candidates_json,
        )

        return self.llm.generate_response(
            system_prompt=prompt,
            response_model=RouterDecision,
        )

    def generate_thesis(self, event: Event) -> Thesis:
        expectation_str = (
            f"Metric: {event.expectation_context.consensus_metric}, "
            f"Expected: {event.expectation_context.expected_value}, "
            f"Actual: {event.expectation_context.actual_value}, "
            f"Surprise: {event.expectation_context.surprise_direction}"
            if event.expectation_context
            else "None"
        )

        prompt = self.prompt_renderer.generate_thesis_prompt(
            event_id=event.id,
            title=event.title,
            content=event.content,
            companies=", ".join(event.companies_mentioned) or "None",
            nature=event.nature.value,
            scope=event.scope.value,
            expectation_context=expectation_str,
        )

        gen_output: ThesisGenerateOutput = self.llm.generate_response(
            system_prompt=prompt,
            response_model=ThesisGenerateOutput,
        )

        now = datetime.now(timezone.utc)
        thesis_id = self._generate_thesis_id(gen_output.ticker)

        evidence_items = [
            EvidenceItem(
                event_id=event.id,
                timestamp=event.published_at,
                point=pt,
            )
            for pt in gen_output.evidence_points
        ]

        counter_evidence_items = [
            EvidenceItem(
                event_id=event.id,
                timestamp=event.published_at,
                point=pt,
            )
            for pt in gen_output.counter_evidence_points
        ]

        thesis = Thesis(
            id=thesis_id,
            ticker=gen_output.ticker,
            core_claim=gen_output.core_claim,
            core_assumptions=gen_output.core_assumptions,
            status=ThesisStatus.ACTIVE,
            strength=gen_output.initial_strength,
            evidence=evidence_items,
            counter_evidence=counter_evidence_items,
            reasoning=gen_output.reasoning,
            created_at=now,
            updated_at=now,
            killed_at=None,
            kill_reason=None,
        )

        self.theses[thesis.id] = thesis
        return thesis

    def update_thesis(self, thesis: Thesis, event: Event) -> Thesis:
        expectation_str = (
            f"Metric: {event.expectation_context.consensus_metric}, "
            f"Expected: {event.expectation_context.expected_value}, "
            f"Actual: {event.expectation_context.actual_value}, "
            f"Surprise: {event.expectation_context.surprise_direction}"
            if event.expectation_context
            else "None"
        )

        prompt = self.prompt_renderer.update_kill_thesis_prompt(
            thesis_id=thesis.id,
            ticker=thesis.ticker,
            core_claim=thesis.core_claim,
            core_assumptions="\n".join(f"- {a}" for a in thesis.core_assumptions),
            strength=thesis.strength,
            evidence_count=len(thesis.evidence),
            counter_evidence_count=len(thesis.counter_evidence),
            event_id=event.id,
            title=event.title,
            content=event.content,
            nature=event.nature.value,
            scope=event.scope.value,
            expectation_context=expectation_str,
        )

        update_output: ThesisUpdateOutput = self.llm.generate_response(
            system_prompt=prompt,
            response_model=ThesisUpdateOutput,
        )

        for pt in update_output.new_evidence_points:
            thesis.evidence.append(
                EvidenceItem(
                    event_id=event.id,
                    timestamp=event.published_at,
                    point=pt,
                )
            )

        for pt in update_output.new_counter_evidence_points:
            thesis.counter_evidence.append(
                EvidenceItem(
                    event_id=event.id,
                    timestamp=event.published_at,
                    point=pt,
                )
            )

        thesis.strength = update_output.new_strength

        now = datetime.now(timezone.utc)
        if update_output.new_status == ThesisStatus.KILLED:
            thesis.status = ThesisStatus.KILLED
            thesis.killed_at = now
            thesis.kill_reason = update_output.kill_reason
            thesis.strength = 0.0

        thesis.reasoning = update_output.updated_reasoning
        thesis.updated_at = now

        self.theses[thesis.id] = thesis
        return thesis

    def process_event(
        self,
        event: Event,
    ) -> Tuple[RouterDecision, Optional[Thesis]]:
        decision = self.route(event)
        result_thesis: Optional[Thesis] = None

        if decision.action == RouterAction.GENERATE_THESIS:
            result_thesis = self.generate_thesis(event)

        elif decision.action == RouterAction.UPDATE_THESIS:
            target_id = decision.target_thesis_id
            if target_id and target_id in self.theses:
                result_thesis = self.update_thesis(self.theses[target_id], event)
            else:
                result_thesis = self.generate_thesis(event)

        elif decision.action == RouterAction.IGNORE:
            result_thesis = None

        self.event_log.append(
            {
                "event_id": event.id,
                "title": event.title,
                "action": decision.action.value,
                "target_thesis_id": decision.target_thesis_id,
                "router_reasoning": decision.reasoning,
                "resulting_thesis_status": (
                    result_thesis.status.value if result_thesis else None
                ),
                "resulting_thesis_strength": (
                    result_thesis.strength if result_thesis else None
                ),
            }
        )

        return decision, result_thesis

    def get_active_theses(self) -> List[Thesis]:
        return [t for t in self.theses.values() if t.status == ThesisStatus.ACTIVE]

    def get_killed_theses(self) -> List[Thesis]:
        return [t for t in self.theses.values() if t.status == ThesisStatus.KILLED]

    def get_thesis(self, thesis_id: str) -> Optional[Thesis]:
        return self.theses.get(thesis_id)

    def get_all_theses(self) -> List[Thesis]:
        return list(self.theses.values())
