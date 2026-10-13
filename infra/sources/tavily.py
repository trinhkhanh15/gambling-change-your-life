from datetime import datetime, timezone
from hashlib import sha256
import os
from typing import Any

from application.ports.source import SourceAdapter
from domain.models.event import Event


class TavilySourceAdapter(SourceAdapter):
    """Turns Tavily search results into the canonical Event contract."""

    def __init__(self, *, api_key: str | None = None, client: Any | None = None):
        if client is not None:
            self._client = client
            return
        key = api_key or os.getenv("TAVILY_API_KEY")
        if not key:
            raise ValueError("TAVILY_API_KEY is required for TavilySourceAdapter")
        try:
            from tavily import TavilyClient
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to use TavilySourceAdapter") from exc
        self._client = TavilyClient(api_key=key)

    def fetch_events(self, query: str, *, limit: int | None = 10) -> list[Event]:
        response = self._client.search(
            query=query,
            max_results=10 if limit is None else limit,
            search_depth="advanced",
            include_raw_content=True,
        )
        events = []
        for result in response.get("results", []):
            title = (result.get("title") or "").strip()
            content = (result.get("raw_content") or result.get("content") or "").strip()
            url = (result.get("url") or "").strip()
            if not title or not content or not url:
                continue
            published_at = self._parse_datetime(result.get("published_date"))
            digest = sha256(url.encode("utf-8")).hexdigest()[:16]
            events.append(
                Event(
                    id=f"tavily-{digest}",
                    published_at=published_at,
                    source=url,
                    title=title,
                    content=content,
                )
            )
        return events

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, str) and value.strip():
            try:
                parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
                return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
            except ValueError:
                pass
        return datetime.now(timezone.utc)
