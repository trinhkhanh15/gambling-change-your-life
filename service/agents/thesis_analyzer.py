from datetime import datetime
from typing import Optional
from domain.schema.event import Event
from domain.schema.thesis import EvidenceItem, Thesis, ThesisStatus
from infra.llm.base import BaseLLMClient


class ThesisAnalyzer:
    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client
        self._counter = 0

    def _generate_thesis_id(self, ticker: str) -> str:
        self._counter += 1
        return f"THESIS-{ticker.upper()}-{self._counter:03d}"

    def generate_thesis(self, event: Event) -> Thesis:
        gen_output = self.llm_client.generate_thesis(event)
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

        now = datetime.utcnow()
        return Thesis(
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

    def update_thesis(self, thesis: Thesis, event: Event) -> Thesis:
        update_output = self.llm_client.update_kill_thesis(event, thesis)

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

        if update_output.new_status == ThesisStatus.KILLED:
            thesis.status = ThesisStatus.KILLED
            thesis.killed_at = datetime.utcnow()
            thesis.kill_reason = update_output.kill_reason
            thesis.strength = 0.0

        thesis.reasoning = update_output.updated_reasoning
        thesis.updated_at = datetime.utcnow()

        return thesis
