from dataclasses import dataclass

from application.ports.repository import Repository
from application.ports.source import SourceAdapter
from domain.models.event import Event
from domain.models.prediction import Prediction
from domain.models.routing import RouterDecision, RouterAction
from domain.models.thesis import Thesis, ThesisStatus
from service.pipelines.layers.analysis_layer import AnalysisLayer
from service.pipelines.layers.prediction_layer import PredictionLayer


@dataclass(frozen=True)
class PipelineResult:
    event: Event
    decision: RouterDecision
    thesis: Thesis | None
    prediction: Prediction | None


class MarketHypothesisPipeline:
    """Small vertical slice: source adapter -> Event -> Thesis -> Prediction."""

    def __init__(
        self,
        *,
        source: SourceAdapter,
        analysis: AnalysisLayer,
        prediction: PredictionLayer,
        repository: Repository,
    ):
        self._source = source
        self._analysis = analysis
        self._prediction = prediction
        self._repository = repository

    def run(self, query: str, *, limit: int = 10) -> list[PipelineResult]:
        results = []
        for event in self._source.fetch_events(query, limit=limit):
            self._repository.save(event)
            decision, thesis = self._analysis.process_event(event)
            prediction = None
            if decision.action == RouterAction.UPDATE_THESIS and thesis is not None and thesis.status == ThesisStatus.KILLED:
                self._prediction.invalidate_for_thesis(thesis.id)
            elif thesis is not None:
                prediction = self._prediction.generate(thesis)
            results.append(
                PipelineResult(
                    event=event,
                    decision=decision,
                    thesis=thesis,
                    prediction=prediction,
                )
            )
        return results
