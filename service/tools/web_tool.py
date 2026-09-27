from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel
from tavily import TavilyClient

from domain.schema.event import Event
from service.pipelines.layers.event_layer import EventLayer


class RawArticle(BaseModel):
    """Dữ liệu thô từ web, chưa phải Event."""
    url: str
    title: str
    content: str
    published_at: Optional[datetime] = None
    source: str


class WebTool:
    def __init__(
        self,
        api_key: str | None = None,
        event_layer: EventLayer | None = None,
    ):
        api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY chưa được cấu hình.")
        self.client = TavilyClient(api_key=api_key)
        self.event_layer = event_layer or EventLayer()

    def search(self, query: str, max_results: int = 5) -> List[RawArticle]:
        """Chỉ fetch thô, chưa phân loại nature/scope."""
        response = self.client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_raw_content=True,
        )

        articles: List[RawArticle] = []
        for result in response.get("results", []):
            url = result.get("url")
            content = result.get("raw_content") or result.get("content") or ""
            if not url or not content:
                continue

            articles.append(RawArticle(
                url=url,
                title=result.get("title", ""),
                content=content,
                published_at=self._parse_date(result.get("published_date")),
                source=urlparse(url).netloc,
            ))
        return articles

    def search_and_decompose(self, query: str, max_results: int = 5) -> List[Event]:
        """Fetch thô rồi convert thành Event chuẩn qua EventLayer."""
        articles = self.search(query, max_results=max_results)
        events: List[Event] = []

        for article in articles:
            decomposed = self.event_layer.decompose_news(
                title=article.title,
                content=article.content,
                source=article.source,
                published_at=article.published_at,
            )
            events.extend(decomposed)

        return events

    @staticmethod
    def _parse_date(value: str | None) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None