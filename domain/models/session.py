from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Thesis(BaseModel):
    """Represents a thesis in the session."""

    content: str
    thinking: str
    evidence: Optional[List[str]] = None
    counter_evidence: Optional[List[str]] = None
    prediction: str
    confidence: float
    created_at: datetime = datetime.now()

class Outcome(BaseModel):
    """Represents the outcome of a session."""

    list_of_theses: List[Thesis]    