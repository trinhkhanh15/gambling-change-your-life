import json
from pathlib import Path
from typing import Union, Dict, List, Any

class SaveTool:
    """
    Role: Local Data & History Persister (Strict JS/JSON).
    task : Tool TẤT CẢ TRONG MỘT để lưu trữ dữ liệu xuống ổ cứng.
    
    QUY TẮC DỮ LIỆU (ONLY JS):
    - KHÔNG truyền object class hay Pydantic Model (như Thesis) vào tool này.
    - Dữ liệu đầu vào bắt buộc phải là Dict hoặc List thuần (đã qua `.model_dump()`).
    """
    
    def __init__(self, base_dir: str = "storage"):
        """
        Khởi tạo thư mục gốc để lưu trữ toàn bộ file JSON và History.
        """
        self._base_path = Path(base_dir)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def append_event_history(self, event_data: Dict[str, Any], filename: str = "event_history.json") -> bool:
        """
        Ghi nối (append) một sự kiện mới vào mảng dữ liệu trong file lịch sử sự kiện.
        
        Args:
            event_data (Dict[str, Any]): Dữ liệu sự kiện thuần JS.
            filename (str): Tên file lịch sử (mặc định 'event_history.json').
            
        //Task
        - Đọc file JSON lên thành List (nếu file chưa có, khởi tạo mảng rỗng `[]`).
        - Dùng `.append(event_data)`.
        - Ghi đè lại mảng mới vào file.
        """
        pass

    def append_prediction_history(self, prediction_data: Dict[str, Any], filename: str = "prediction_history.json") -> bool:
        """
        Ghi nối (append) một kết quả dự đoán mới vào mảng dữ liệu trong file lịch sử dự đoán.
        
        Args:
            prediction_data (Dict[str, Any]): Dữ liệu dự đoán thuần JS.
            filename (str): Tên file lịch sử (mặc định 'prediction_history.json').
            
        //Task
        - Tương tự như hàm append_event_history.
        """
        pass

    def save_json_overwrite(self, data: Union[Dict[str, Any], List[Any]], filename: str) -> bool:
        """
        Lưu đè (overwrite) toàn bộ dữ liệu thành một file JSON mới.
        Thường dùng khi muốn xuất báo cáo riêng lẻ hoặc lưu file cache tạm thời.
        
        Args:
            data (Union[Dict, List]): Dữ liệu thuần JS.
            filename (str): Tên file đích (ví dụ: 'report_q3.json').
            
        //Task
        - Nối thư mục _base_path với filename.
        - Mở file chế độ 'w', dùng json.dump(indent=4, ensure_ascii=False).
        """
        pass