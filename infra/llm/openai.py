from pydantic import BaseModel
from typing import Optional


def generate_response(
    system_prompt: str,
    response_model: Optional[BaseModel] = None,
) -> str:
    """Generate a response from the OpenAI API using the provided system prompt."""

    if response_model:
        return _generate_structured(system_prompt, response_model)
    return _generate_plain(system_prompt)


def _generate_plain(
    system_prompt: str,
) -> str:
    """Generate a plain text response from the OpenAI API using the provided system prompt."""

    pass


def _generate_structured(
    system_prompt: str,
    response_model: BaseModel,
) -> BaseModel:
    """Generate a structured response from the OpenAI API using the provided system prompt and response model."""

    pass

