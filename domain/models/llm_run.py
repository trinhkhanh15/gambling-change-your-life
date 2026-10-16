from datetime import date, datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class LLMRun(BaseModel):
    """Token usage and cost of one real-LLM replay run."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    run_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model: str = Field(min_length=1)
    start_date: date
    end_date: date
    llm_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_usd: float | None = None  # None when OPENAI_*_COST_PER_1M are not set
