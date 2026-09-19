import os
from typing import Dict, List

from tavily import TavilyClient


class WebTool:
    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY is not set. "
                "Pass api_key to WebTool() or set the environment variable."
            )

        self.client = TavilyClient(api_key=api_key)

    def web_search(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[str]:
        """Search the web and return a list of URLs."""
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
            )

            return [
                result["url"]
                for result in response.get("results", [])
                if result.get("url")
            ]

        except Exception as e:
            print(f"Web search failed: {e}")
            return []

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 5,
    ) -> Dict[str, str]:
        """
        Search the web and return content in the old format:

        {
            "https://example.com/article": "article content...",
            ...
        }
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                include_raw_content=True,
            )

            results: Dict[str, str] = {}

            for result in response.get("results", []):
                url = result.get("url")

                # Prefer full extracted page content.
                # Fall back to Tavily's search-result content.
                content = (
                    result.get("raw_content")
                    or result.get("content")
                    or ""
                )

                if url and content:
                    results[url] = content

            return results

        except Exception as e:
            print(f"Search and fetch failed: {e}")
            return {}