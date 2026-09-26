from collections.abc import Sequence

from domain.models.event import Event


class InMemorySourceAdapter:
    def __init__(self, events: Sequence[Event]):
        self._events = list(events)

    def fetch_events(self, query: str, *, limit: int = 10) -> list[Event]:
        del query  # Fixtures are selected by the caller, not a search engine.
        return self._events[:limit]
