from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone

from application.ports.repository import Repository
from application.ports.source import SourceAdapter
from domain.models.evaluation import Evaluation
from domain.models.event import Event
from domain.models.prediction import Prediction, PredictionStatus
from domain.models.reality import Reality
from domain.models.routing import RouterDecision, RouterAction
from domain.models.thesis import Thesis, ThesisStatus
from service.pipelines.layers.analysis_layer import AnalysisLayer
from service.pipelines.layers.evaluation_layer import EvaluationLayer
from service.pipelines.layers.event_layer import EventLayer
from service.pipelines.layers.prediction_layer import PredictionLayer
from infra.sources.stock_prices import StockPriceOutcomeResolver


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
        outcome_resolver: StockPriceOutcomeResolver | None = None,
        evaluation: EvaluationLayer | None = None,
        event_layer: EventLayer | None = None,
    ):
        self._event_layer = event_layer
        self._source = source
        self._analysis = analysis
        self._prediction = prediction
        self._repository = repository
        self._outcome_resolver = outcome_resolver
        self._evaluation = evaluation
        if outcome_resolver is not None and evaluation is None:
            raise ValueError("evaluation is required when an outcome resolver is configured")

    def run(
        self,
        query: str = "",
        *,
        limit: int | None = 10,
        start_date: date | None = None,
        end_date: date | None = None,
        on_result: Callable[[int, int, PipelineResult], None] | None = None,
        skip_processed: bool = False,
    ) -> list[PipelineResult]:
        if (start_date is None) != (end_date is None):
            raise ValueError("start_date and end_date must be provided together")
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("start_date must be on or before end_date")
        results = []
        events = sorted(
            self._source.fetch_events(query, limit=limit),
            key=lambda item: (item.published_at, item.id),
        )
        if start_date is not None and end_date is not None:
            events = [
                event
                for event in events
                if start_date <= self._utc_date(event.published_at) <= end_date
            ]

        # shortcut: an event counts as done once any of its parts was saved; a crash between two parts
        # of one split news item skips the rest of it on resume. Upgrade to a per-event done marker if it bites.
        done = {item.id.split("#")[0] for item in self._repository.list(Event)} if skip_processed else set()
        for index, source_event in enumerate(events, start=1):
            if source_event.id in done:
                continue
            parts = self._event_layer.decompose(source_event) if self._event_layer else [source_event]
            for event in parts:
                result = self._process_event(event)
                self._repository.save(event)  # saved only once fully processed: this is the resume marker
                results.append(result)
                if on_result is not None:
                    on_result(index, len(events), result)
        if self._outcome_resolver is not None and self._outcome_resolver.latest_date is not None:
            self._resolve_due(self._outcome_resolver.latest_date, include_same_day=True)
        return results

    def _process_event(self, event: Event) -> PipelineResult:
        self._resolve_due(event.published_at.date(), include_same_day=False)
        decision, thesis = self._analysis.process_event(event)
        prediction = None
        if decision.action == RouterAction.UPDATE_THESIS and thesis is not None and thesis.status == ThesisStatus.KILLED:
            self._prediction.invalidate_for_thesis(thesis.id)
        elif thesis is not None:
            active_predictions = [
                item
                for item in self._repository.list(Prediction)
                if item.thesis_id == thesis.id and item.status == PredictionStatus.ACTIVE
            ]
            if self._outcome_resolver is not None and active_predictions:
                # Keep the original forecast alive until its market horizon resolves.
                prediction = max(active_predictions, key=lambda item: item.version)
                return PipelineResult(event, decision, thesis, prediction)
            market_context = None
            if self._outcome_resolver is not None:
                context = self._outcome_resolver.forecast_context(thesis.ticker, event.published_at)
                if context is None:
                    return PipelineResult(event, decision, thesis, None)
                market_context = context.prediction_fields()
            prediction = self._prediction.generate(
                thesis,
                market_context=market_context,
                information_cutoff=event.published_at,
            )
        return PipelineResult(event, decision, thesis, prediction)

    @staticmethod
    def _utc_date(value: datetime) -> date:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).date()

    def _resolve_due(self, as_of, *, include_same_day: bool) -> list[Evaluation]:
        if self._outcome_resolver is None or self._evaluation is None:
            return []
        evaluations = []
        for prediction in self._repository.list(Prediction):
            due = (
                prediction.horizon_end <= as_of
                if include_same_day
                else prediction.horizon_end < as_of
            )
            if prediction.status != PredictionStatus.ACTIVE or not due:
                continue
            reality = self._outcome_resolver.resolve(prediction)
            if reality is not None:
                evaluations.append(self._evaluation.evaluate(prediction, reality))
        return evaluations
