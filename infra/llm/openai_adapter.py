import os
from typing import TypeVar

from pydantic import BaseModel

from application.ports.llm import LLMClient

T = TypeVar("T", bound=BaseModel)


class OpenAIAdapter(LLMClient):
    """OpenAI structured-output adapter; imports provider packages lazily."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-5.6-luna"):
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

    @property
    def model_name(self) -> str:
        return self._model

    def generate_response(self, *, system_prompt: str, response_model: type[T]) -> T:
        kwargs = {}
        if any(keyword in self._model for keyword in ("luna", "o3", "o4", "gpt-5")):
            kwargs["reasoning_effort"] = "none"

        try:
            return self._client.chat.completions.create(
                model=self._model,
                response_model=response_model,
                messages=[{"role": "system", "content": system_prompt}],
                **kwargs,
            )
        except Exception as exc:
            if "reasoning_effort" in kwargs and "reasoning_effort" in str(exc):
                return self._client.chat.completions.create(
                    model=self._model,
                    response_model=response_model,
                    messages=[{"role": "system", "content": system_prompt}],
                )
            raise
