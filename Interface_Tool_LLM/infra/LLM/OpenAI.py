from pydantic import BaseModel
from typing import Optional, Type, Union, Any

class OpenAIClient:
    """
    Role: Reasoning & Prediction Engine.
    Nhận prompt đã render từ PromptRenderer và bắt buộc trả về dữ liệu chuẩn Pydantic Model để luồng Python 
    có thể đọc và tính toán Brier Score.
    """

    def __init__(self, api_key: str, default_model: str = "gpt-4o-mini"):
        # Setup OpenAI and Instructor wrapper here
        pass
        
    def generate_response(
        self,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> Union[str, Any]:
        """
        Sends the rendered prompt to OpenAI and enforces structured output.
        
        Args:
            system_prompt (str): The fully rendered prompt from PromptRenderer.
            response_model (Type[BaseModel]): The Pydantic class defining the expected 
                                              JSON structure (e.g., AnalyseOutput).
                                              
        Returns:
            A validated Pydantic object if response_model is provided, else plain text.
        """
        pass