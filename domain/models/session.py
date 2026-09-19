from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Thesis(BaseModel):
    """Represents a thesis in the session."""

    content: str # What happened or what is being claimed
    thinking: str # The reasoning or thought process behind the thesis
    
    prediction: str # The prediction of what will happen next based on the thesis
    evidence: Optional[List[str]] = None # Which evidence supports the thesis
    counter_evidence: Optional[List[str]] = None  # Which evidence contradicts the thesis
    confidence: float

    created_at: datetime = datetime.now()