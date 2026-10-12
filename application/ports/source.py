from typing import Protocol

from domain.models.event import Event


class SourceAdapter(Protocol):
    def fetch_events(self, query: str, *, limit: int = 10) -> list[Event]: ...
