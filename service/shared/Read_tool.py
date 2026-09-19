import json
from pathlib import Path
from typing import Union, Dict, List, Any, Optional

class ReadTool:
    """
    Role: Local Data Loader (Strict JS/JSON).
    Yêu cầu: Đọc ngược các file JSON (Event, Prediction, History) từ ổ cứng lên.
    
    ⚠️ QUY TẮC DỮ LIỆU:
    Dữ liệu trả về luôn là Dict/List thuần. Nếu team Model cần tính toán, 
    họ phải tự đưa cái Dict này vào lại Pydantic Model (ví dụ: `Thesis(**data)`).
    """
    
    def __init__(self, base_dir: str = "storage"):
        self._base_path = Path(base_dir)

    def read_json(self, filename: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Đọc file JSON lên thành cấu trúc Dict/List thuần của Python.
        
        Args:
            filename (str): Tên file cần đọc.
            
        Returns:
            Optional[Union[Dict, List]]: Trả về Dict/List nếu thành công, None nếu file không tồn tại.
        """
        pass