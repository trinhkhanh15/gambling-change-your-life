from typing import Dict, List, Optional, Tuple
from src.analysis import ThesisAnalyzer
from src.llm_client import BaseLLMClient, get_llm_client
from src.router import ThesisRouter
from src.schema import (
    Event,
    RouterAction,
    RouterDecision,
    Thesis,
    ThesisStatus,
)


class AnalysisPipeline:
    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or get_llm_client()
        self.router = ThesisRouter(self.llm_client)
        self.analyzer = ThesisAnalyzer(self.llm_client)
        self.theses: Dict[str, Thesis] = {}
        self.event_log: List[Dict] = []

    def get_active_theses(self) -> List[Thesis]:
        return [t for t in self.theses.values() if t.status == ThesisStatus.ACTIVE]

    def get_killed_theses(self) -> List[Thesis]:
        return [t for t in self.theses.values() if t.status == ThesisStatus.KILLED]

    def process_event(self, event: Event) -> Tuple[RouterDecision, Optional[Thesis]]:
        active_theses = self.get_active_theses()
        decision = self.router.route(event, active_theses)

        result_thesis: Optional[Thesis] = None

        if decision.action == RouterAction.GENERATE_THESIS:
            new_thesis = self.analyzer.generate_thesis(event)
            self.theses[new_thesis.id] = new_thesis
            result_thesis = new_thesis

        elif decision.action == RouterAction.UPDATE_THESIS:
            target_id = decision.target_thesis_id
            if target_id and target_id in self.theses:
                target_thesis = self.theses[target_id]
                updated_thesis = self.analyzer.update_thesis(target_thesis, event)
                self.theses[target_id] = updated_thesis
                result_thesis = updated_thesis
            else:
                new_thesis = self.analyzer.generate_thesis(event)
                self.theses[new_thesis.id] = new_thesis
                result_thesis = new_thesis

        elif decision.action == RouterAction.IGNORE:
            result_thesis = None

        self.event_log.append({
            "event_id": event.id,
            "title": event.title,
            "action": decision.action.value,
            "target_thesis_id": decision.target_thesis_id,
            "router_reasoning": decision.reasoning,
            "resulting_thesis_status": result_thesis.status.value if result_thesis else None,
            "resulting_thesis_strength": result_thesis.strength if result_thesis else None,
        })

        return decision, result_thesis
