from typing import Dict

class WebTool:
    """
    Role: External Data Fetcher (Scraper).
    Dành cho team Pipeline: Gọi tool này ở đầu luồng để thu thập báo cáo tài chính, 
    tin tức vĩ mô theo thời gian thực (Time-locked).
    """

    def __init__(self):
        # Setup API keys for Tavily
        pass

    def search_and_fetch(self, query: str, max_results: int = 3) -> Dict[str, str]:
        """
        Searches the web and extracts raw text content from the top results.
        
        Args:
            query (str): The search intent (e.g., "NVIDIA Q3 2025 earnings context").
            max_results (int): Number of sources to aggregate.
            
        Returns:
            Dict[str, str]: A dictionary mapping source URLs to their cleaned text content.
        """
        pass