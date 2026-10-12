from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    def generate_response(self, *, system_prompt: str, response_model: type[T]) -> T: ...
