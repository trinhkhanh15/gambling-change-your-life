from pydantic import BaseModel
from typing import Optional, Type, Union, Any
from openai import OpenAI
import instructor

class OpenAIClient:
    """A client for interacting with the OpenAI API."""

    def __init__(self, api_key: str, default_model: str = "gpt-5.4-mini"):
        self._client = OpenAI(api_key=api_key)
        # Bọc OpenAI client bằng instructor để hỗ trợ structured outputs
        self._instructor = instructor.from_openai(self._client)
        self._default_model = default_model
        
    def generate_response(
        self,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> Union[str, Any]:
        """Generate a response from the OpenAI API using the provided system prompt."""
        if response_model:
            return self._generate_structured(system_prompt, response_model)
        return self._generate_plain(system_prompt)

    def _generate_plain(
        self,   
        system_prompt: str,
    ) -> str:
        """Generate a plain text response from the OpenAI API using the provided system prompt."""
        response = self._client.chat.completions.create(
            model=self._default_model,
            messages=[
                {"role": "system", "content": system_prompt}
            ]
        )
        return response.choices[0].message.content

    def _generate_structured(
        self,
        system_prompt: str,
        response_model: Type[BaseModel],
    ) -> Any:
        """Generate a structured response from the OpenAI API using the provided system prompt and response model."""
        response = self._instructor.chat.completions.create(
            model=self._default_model,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt}
            ]
        )
        return response