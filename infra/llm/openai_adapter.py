import os
from typing import TypeVar

from pydantic import BaseModel

from application.ports.llm import LLMClient

T = TypeVar("T", bound=BaseModel)


class OpenAIAdapter(LLMClient):
    """OpenAI structured-output adapter; imports provider packages lazily."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-5.4-mini"):
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIAdapter")

        try:
            import instructor
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to use OpenAIAdapter") from exc

        self._client = instructor.from_openai(OpenAI(api_key=resolved_key))
        self._model = model

    def generate_response(self, *, system_prompt: str, response_model: type[T]) -> T:
        return self._client.chat.completions.create(
            model=self._model,
            response_model=response_model,
            messages=[{"role": "system", "content": system_prompt}],
        )
