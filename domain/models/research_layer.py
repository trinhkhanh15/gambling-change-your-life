from typing import Dict, List, Optional
from pydantic import BaseModel

class ResearchInput(BaseModel):
    """Represents the input for the research layer."""

    fetched_data: Dict[str, str]
    max_theses_count: int

class ResearchItem(BaseModel):
    """Represents the item for the research layer."""

    content: str
    thinking: str
    search_queries: List[str]


    