import os
from typing import Optional, Union
from infra.llm.mock import MockLLMClient

try:
    from infra.llm.openai import OpenAIClient
except ImportError:
    OpenAIClient = None


def get_llm_client(api_key: Optional[str] = None) -> Union[OpenAIClient, MockLLMClient]:
    key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key and OpenAIClient is not None:
        try:
            return OpenAIClient(api_key=key)
        except Exception:
            pass
    return MockLLMClient()


__all__ = [
    "MockLLMClient",
    "OpenAIClient",
    "get_llm_client",
]
