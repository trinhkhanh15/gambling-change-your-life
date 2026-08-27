from typing import List, Optional, Dict
from pydantic import BaseModel

class AnalyseInput(BaseModel):
    """Represents the input for the analysis layer."""

    content: str
    thinking: str
    research_data: Dict[str, str]

class AnalyseOutput(BaseModel):
    """Represents the output of the analysis layer."""

    prediction: str
    evidence: Optional[List[str]] = None
    counter_evidence: Optional[List[str]] = None
    confidence: float