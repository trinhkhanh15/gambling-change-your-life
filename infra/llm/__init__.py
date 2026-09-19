import os
from infra.llm.base import BaseLLMClient
from infra.llm.mock import MockFinancialLLMClient

try:
    from infra.llm.openai import OpenAIClient
except ImportError:
    OpenAIClient = None


def get_llm_client() -> BaseLLMClient:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key and OpenAIClient is not None:
        try:
            return OpenAIClient(api_key=api_key)
        except Exception:
            pass
    return MockFinancialLLMClient()


__all__ = [
    "BaseLLMClient",
    "MockFinancialLLMClient",
    "OpenAIClient",
    "get_llm_client",
]
