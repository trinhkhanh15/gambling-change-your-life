from abc import ABC, abstractmethod
from typing import List
from domain.schema.event import Event
from domain.schema.router import RouterDecision, ThesisGenerateOutput, ThesisUpdateOutput
from domain.schema.thesis import Thesis


class BaseLLMClient(ABC):
    @abstractmethod
    def route_event(self, event: Event, candidate_theses: List[Thesis]) -> RouterDecision:
        pass

    @abstractmethod
    def generate_thesis(self, event: Event) -> ThesisGenerateOutput:
        pass

    @abstractmethod
    def update_kill_thesis(self, event: Event, thesis: Thesis) -> ThesisUpdateOutput:
        pass
