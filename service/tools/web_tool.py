from typing import List, Optional, Dict

import requests
from bs4 import BeautifulSoup
from googlesearch import search

class WebTool:
    def __init__(self, timeout: int = 10):
        # Đặt thời gian chờ tối đa cho các request
        self.timeout = timeout
        # Giả mạo User-Agent giống trình duyệt thật để tránh bị các trang web chặn (Lỗi 403)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def web_search(self, query: str, max_results: int) -> List[str]:
        """Perform a web search for the given query and return a list of URLs."""
        try:
            # Trả về danh sách các URL từ kết quả tìm kiếm Google
            urls = search(query, num=max_results, stop=max_results, pause=2.0)
            return list(urls)
        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {e}")
            return []

    def fetch_data(self, url: str) -> str:
        """Fetch data from the given URL and return it as a string."""
        try:
            # Gửi HTTP GET request tới URL
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()  # Ném lỗi nếu HTTP status code không phải là 2xx (ví dụ: 404, 500)
            
            # Sử dụng BeautifulSoup để parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Xóa các thẻ script và style vì chúng không chứa văn bản đọc được
            for script in soup(["script", "style"]):
                script.extract()
                
            # Lấy toàn bộ văn bản từ trang web, các đoạn văn cách nhau bằng khoảng trắng
            text = soup.get_text(separator=' ', strip=True)
            return text
            
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi tải URL {url}: {e}")
            return ""

    def search_and_fetch(self, query: str, max_results: int = 5) -> Dict[str, str]:
        """Search for a query and fetch data from the resulting URLs."""
        urls = self.web_search(query, max_results)
        
        # Lấy nội dung từ từng URL (loại bỏ các kết quả rỗng nếu fetch bị lỗi)
        results = {}
        for url in urls:
            data = self.fetch_data(url)
            if data:
                results[url] = data
                
        return results