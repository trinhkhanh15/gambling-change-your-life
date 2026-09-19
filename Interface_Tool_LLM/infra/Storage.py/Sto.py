import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class JsonStorage:
    """
    Local JSON Persistence Layer (No Database).
    
    QUY TẮC DỮ LIỆU BẮT BUỘC (STRICT JS/JSON ONLY):
    - KHÔNG nhận hoặc xử lý các Pydantic model hay custom class.
    - Tất cả input/output đều là kiểu dữ liệu thuần JS/JSON (Dict, List, str, int, float, bool).
    - Phía gọi (Pipeline/Model) phải tự convert model thành Dict/List (ví dụ: .model_dump()) 
      trước khi nạp vào Storage.
    """

    def __init__(self, storage_dir: str = "data_storage"):
        """
        Khởi tạo thư mục lưu trữ file JSON.
        
        Args:
            storage_dir (str): Đường dẫn thư mục chứa file.
        """
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def save_event_history(self, event_data: Dict[str, Any], filename: str = "event_history.json") -> bool:
        """
        Lưu/Ghi nối (append) dữ liệu sự kiện (event history) vào file JSON.

        Args:
            event_data (Dict[str, Any]): Dữ liệu sự kiện thuần JS/JSON.
            filename (str): Tên file lưu trữ sự kiện.

        Returns:
            bool: True nếu ghi file thành công, False nếu thất bại.

        // Task:
        - Đọc danh sách sự kiện hiện có từ file (nếu chưa có file thì tạo mảng rỗng `[]`).
        - Nối `event_data` vào danh sách.
        - Ghi đè lại toàn bộ mảng vào file với `indent=4` và `ensure_ascii=False`.
        """
        pass

    def load_event_history(self, filename: str = "event_history.json") -> List[Dict[str, Any]]:
        """
        Đọc toàn bộ lịch sử sự kiện từ file JSON.

        Args:
            filename (str): Tên file sự kiện cần đọc.

        Returns:
            List[Dict[str, Any]]: Danh sách các sự kiện thuần JS/JSON.
                                  Trả về mảng rỗng `[]` nếu file chưa tồn tại hoặc bị lỗi.

        // Task:
        - Kiểm tra file tồn tại.
        - Đọc file bằng json.load() với encoding='utf-8'.
        - Xử lý các lỗi ngoại lệ (FileNotFoundError, json.JSONDecodeError).
        """
        pass

    def save_prediction_history(self, prediction_data: Dict[str, Any], filename: str = "prediction_history.json") -> bool:
        """
        Lưu/Ghi nối (append) kết quả dự đoán (prediction) vào file JSON.

        Args:
            prediction_data (Dict[str, Any]): Dữ liệu dự đoán thuần JS/JSON.
            filename (str): Tên file lưu trữ dự đoán.

        Returns:
            bool: True nếu ghi file thành công, False nếu thất bại.

        // Task:
        - Đọc danh sách dự đoán hiện có từ file (nếu chưa có file thì tạo mảng rỗng `[]`).
        - Nối `prediction_data` vào danh sách.
        - Ghi đè lại toàn bộ mảng vào file với `indent=4` và `ensure_ascii=False`.
        """
        pass

    def load_prediction_history(self, filename: str = "prediction_history.json") -> List[Dict[str, Any]]:
        """
        Đọc toàn bộ lịch sử dự đoán từ file JSON để phục vụ việc đánh giá/chấm điểm.

        Args:
            filename (str): Tên file dự đoán cần đọc.

        Returns:
            List[Dict[str, Any]]: Danh sách các dự đoán thuần JS/JSON.
                                  Trả về mảng rỗng `[]` nếu file chưa tồn tại hoặc bị lỗi.

        // Task:
        - Tương tự như load_event_history, đọc và parse JSON an toàn.
        """
        pass