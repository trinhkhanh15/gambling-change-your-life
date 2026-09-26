from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EventNature(str, Enum):
    FACT = "fact"
    EXPECTATION = "expectation"


class EventScope(str, Enum):
    COMPANY = "company"
    INDUSTRY = "industry"
    MACRO = "macro"


class ExpectationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    consensus_metric: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None
    surprise_direction: str | None = None


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    companies_mentioned: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    nature: EventNature = EventNature.FACT
    scope: EventScope = EventScope.COMPANY
    expectation_context: ExpectationContext | None = None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(min_length=1)
    timestamp: datetime
    point: str = Field(min_length=1)
