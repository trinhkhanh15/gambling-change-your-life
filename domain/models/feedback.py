from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Feedback(BaseModel):
    """Represents feedback provided by the data."""

    agent_prediction: str
    actual_happened: str
    matching_score: float
    reasoning: str
    confidence: float
    datetime: datetime = datetime.now()