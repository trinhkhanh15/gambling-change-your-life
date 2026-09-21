from typing import Optional, Type, Union, Any
from openai import OpenAI
from pydantic import BaseModel
import instructor


class OpenAIClient:
    def __init__(self, api_key: str, default_model: str = "gpt-5.4-mini"):
        self._client = OpenAI(api_key=api_key)
        self._instructor = instructor.from_openai(self._client)
        self._default_model = default_model

    def generate_response(
        self,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> Union[str, Any]:
        if response_model:
            return self._generate_structured(system_prompt, response_model)
        return self._generate_plain(system_prompt)

    def _generate_plain(
        self,
        system_prompt: str,
    ) -> str:
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
        response = self._instructor.chat.completions.create(
            model=self._default_model,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt}
            ]
        )
        return response