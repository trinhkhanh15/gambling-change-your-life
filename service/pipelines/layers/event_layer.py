import logging

from application.ports.llm import LLMClient
from domain.models.event import Event, EventDecomposition
from domain.prompts import render_prompt

logger = logging.getLogger(__name__)


class EventLayer:
    """Splits a news item that carries several distinct developments into atomic events."""

    def __init__(self, llm: LLMClient):
        self._llm = llm

    def decompose(self, event: Event) -> list[Event]:
        prompt = render_prompt(
            "decompose_event",
            {
                "title": event.title,
                "content": event.content,
                "source": event.source,
                "known_companies": event.companies_mentioned,
            },
        )
        try:
            parts = EventDecomposition.model_validate(
                self._llm.generate_response(system_prompt=prompt, response_model=EventDecomposition)
            ).events
        except Exception as exc:  # a failed split must not abort a long replay
            logger.warning("event decomposition failed for %s, using it as-is: %s", event.id, exc)
            return [event]
        if len(parts) == 1:
            return [event]  # keep the original text instead of the LLM's rewrite

        known = {company.upper() for company in event.companies_mentioned}
        events = []
        for index, part in enumerate(parts, start=1):
            companies = [c for c in part.companies_mentioned if c.upper() in known]
            events.append(
                event.model_copy(
                    update={
                        "id": f"{event.id}#{index}",
                        "title": part.title,
                        "content": part.content,
                        "companies_mentioned": companies or event.companies_mentioned,
                        "sectors": part.sectors or event.sectors,
                        "nature": part.nature,
                        "scope": part.scope,
                        "expectation_context": part.expectation_context,
                    }
                )
            )
        return events
