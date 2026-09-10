from typing import List
from src.llm_client import BaseLLMClient
from src.schema import Event, RouterDecision, Thesis, ThesisStatus


class ThesisRouter:
    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def filter_candidate_theses(self, event: Event, active_theses: List[Thesis], top_k: int = 5) -> List[Thesis]:
        candidates = []
        event_tickers = {t.upper() for t in event.companies_mentioned}
        event_text = (event.title + " " + event.content).lower()

        for thesis in active_theses:
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

    def route(self, event: Event, all_active_theses: List[Thesis]) -> RouterDecision:
        candidate_theses = self.filter_candidate_theses(event, all_active_theses)
        return self.llm_client.route_event(event, candidate_theses)
