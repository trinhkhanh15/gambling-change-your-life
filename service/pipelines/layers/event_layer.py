from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional, Union

from domain.schema.event import (
    DecomposedEventItem,
    Event,
    EventDecompositionOutput,
    EventNature,
    EventScope,
    ExpectationContext,
)
from infra.llm import get_llm_client
from service.shared.prompt_renderer import PromptRenderer


class EventLayer:
    def __init__(
        self,
        llm_client: Any | None = None,
        prompt_renderer: PromptRenderer | None = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.prompt_renderer = prompt_renderer or PromptRenderer()
        self._counter = 0

    def _generate_event_id(self, prefix: str = "EVT") -> str:
        self._counter += 1
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._counter:04d}"

    def create_event(
        self,
        title: str,
        content: str,
        source: str = "manual",
        published_at: datetime | None = None,
        companies_mentioned: list[str] | None = None,
        sectors: list[str] | None = None,
        nature: EventNature = EventNature.FACT,
        scope: EventScope = EventScope.COMPANY,
        expectation_context: ExpectationContext | None = None,
        event_id: str | None = None,
    ) -> Event:
        now = datetime.now(timezone.utc)
        return Event(
            id=event_id or self._generate_event_id(),
            published_at=published_at or now,
            source=source,
            title=title,
            content=content,
            companies_mentioned=companies_mentioned or [],
            sectors=sectors or [],
            nature=nature,
            scope=scope,
            expectation_context=expectation_context,
        )

    def validate_event(self, data: Event | dict) -> Event:
        if isinstance(data, Event):
            return data
        return Event.model_validate(data)

    def decompose_news(
        self,
        title: str,
        content: str,
        source: str = "news",
        published_at: datetime | None = None,
    ) -> List[Event]:
        now = published_at or datetime.now(timezone.utc)
        try:
            prompt = self.prompt_renderer.decompose_event_prompt(
                title=title,
                content=content,
                source=source,
            )
            output: EventDecompositionOutput = self.llm.generate_response(
                system_prompt=prompt,
                response_model=EventDecompositionOutput,
            )
            if output and output.events:
                events = []
                for item in output.events:
                    evt_id = self._generate_event_id()
                    events.append(
                        Event(
                            id=evt_id,
                            published_at=now,
                            source=source,
                            title=item.title,
                            content=item.content,
                            companies_mentioned=item.companies_mentioned,
                            sectors=item.sectors,
                            nature=item.nature,
                            scope=item.scope,
                            expectation_context=item.expectation_context,
                        )
                    )
                return events
        except Exception:
            pass

        return [
            self.create_event(
                title=title,
                content=content,
                source=source,
                published_at=now,
            )
        ]

    def process(
        self,
        raw_input: Union[Event, dict, List[Union[Event, dict]]],
    ) -> List[Event]:
        if isinstance(raw_input, list):
            return [self.validate_event(item) for item in raw_input]
        return [self.validate_event(raw_input)]
