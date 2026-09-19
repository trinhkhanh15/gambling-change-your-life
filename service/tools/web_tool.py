import os
import json
from pathlib import Path
from typing import Dict, List

from tavily import TavilyClient


class WebTool:
    """
    Role: External Data Fetcher (Scraper).
    Target Audience: Pipeline Engineering Team.
    Purpose: Initializes at the beginning of the execution flow to aggregate 
    financial reports and macroeconomic news in real-time.
    """

    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY is not set. "
                "Provide the api_key during WebTool instantiation or set it as an environment variable."
            )

        self.client = TavilyClient(api_key=api_key)

    def web_search(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[str]:
        """
        Executes a basic web search and retrieves a list of relevant source URLs.
        """
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
            print(f"[-] Web search execution failed: {e}")
            return []

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 5,
    ) -> Dict[str, str]:
        """
        Executes an advanced web search and extracts raw Markdown/HTML content.
        Retains original formatting (tables, headers, links) to optimize LLM contextual parsing.
        """
        try:
            print(f"[*] Sending request to Tavily API for query: '{query}'...")
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                include_raw_content=True,
            )

            results: Dict[str, str] = {}

            for result in response.get("results", []):
                url = result.get("url")

                # Prioritize 'raw_content' to preserve structural markers for the LLM. 
                # Fallback to standard 'content' if the target domain restricts raw extraction.
                content = (
                    result.get("raw_content")
                    or result.get("content")
                    or ""
                )

                if url and content:
                    results[url] = content

            print(f"[+] Successfully retrieved {len(results)} source(s).")
            return results

        except Exception as e:
            print(f"[-] Search and fetch execution failed: {e}")
            return {}


# ==========================================
# EXPORT TO JSON BLOCK (For testing & verifying raw content)
# ==========================================
if __name__ == "__main__":
    from dotenv import load_dotenv

    # Load environment variables (TAVILY_API_KEY)
    load_dotenv()

    print("Initializing WebTool...")
    tool = WebTool()

    test_query = "NVIDIA Q1 2024 financial results"
    # Lấy 2 kết quả để đảm bảo file có nhiều nguồn dữ liệu
    fetched_data = tool.search_and_fetch(test_query, max_results=2)

    if fetched_data:
        # Tự động tạo file raw_content.json nằm cùng thư mục với file code này
        output_path = Path(__file__).parent / "raw_content.json"
        
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(fetched_data, file, ensure_ascii=False, indent=4)
            
        print(f"✅ SUCCESS: Raw Markdown data has been exported to '{output_path.name}'.")
    else:
        print("❌ FAILED: No data was fetched. Check your API key or network connection.")