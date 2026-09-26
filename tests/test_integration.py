from datetime import datetime, timezone

from domain.models.event import Event
from domain.models.prediction import Direction, Prediction, PredictionStatus
from domain.models.routing import RouterAction
from domain.models.reality import Reality
from infra.llm.mock import MockLLMClient
from infra.sources.in_memory import InMemorySourceAdapter
from infra.storage.json_repository import JsonRepository
from service.pipelines.layers.analysis_layer import AnalysisLayer
from service.pipelines.layers.evaluation_layer import EvaluationLayer
from service.pipelines.layers.prediction_layer import PredictionLayer
from service.pipelines.pipeline import MarketHypothesisPipeline


def test_source_to_evaluation_flow_persists_records(tmp_path):
    repository = JsonRepository(tmp_path / "records.json")
    llm = MockLLMClient()
    event = Event(
        id="evt-1",
        published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
        source="fixture",
        title="ACME raises revenue guidance after strong demand",
        content="ACME reports demand growth and raises full-year revenue guidance.",
        companies_mentioned=["ACME"],
    )
    pipeline = MarketHypothesisPipeline(
        source=InMemorySourceAdapter([event]),
        analysis=AnalysisLayer(llm, repository),
        prediction=PredictionLayer(llm, repository),
        repository=repository,
    )

    [result] = pipeline.run("ACME", limit=1)
    assert result.thesis.id == result.prediction.thesis_id
    assert result.prediction.version == 1
    assert result.prediction.status == PredictionStatus.ACTIVE

    reality = Reality(
        id="reality-1",
        prediction_id=result.prediction.id,
        target=result.prediction.target,
        metric=result.prediction.metrics[0],
        baseline=result.prediction.baseline,
        actual_value=105.0,
        actual_direction=Direction.UP,
        observed_at=datetime(2026, 10, 4, tzinfo=timezone.utc),
        source="fixture",
        reasoning="The observed price increased over the horizon.",
        actual_drivers=["demand", "guidance"],
    )
    evaluation = EvaluationLayer(repository).evaluate(result.prediction, reality)

    assert evaluation.direction_score == 1.0
    assert evaluation.magnitude_score == 1.0
    assert evaluation.reason_score == 1.0
    assert evaluation.matching_score == 1.0

    reloaded = JsonRepository(tmp_path / "records.json")
    assert reloaded.get(Event, event.id) == event
    assert reloaded.get(Prediction, result.prediction.id).status == PredictionStatus.RESOLVED
    assert reloaded.get(type(evaluation), evaluation.id) == evaluation


def test_tavily_adapter_normalizes_search_results():
    from infra.sources.tavily import TavilySourceAdapter

    class FakeTavily:
        def search(self, **kwargs):
            assert kwargs["query"] == "ACME earnings"
            return {
                "results": [
                    {
                        "title": "ACME reports growth",
                        "url": "https://example.test/acme",
                        "published_date": "2026-09-20T10:00:00Z",
                        "content": "Short content",
                        "raw_content": "Full report content",
                    },
                    {"url": "https://example.test/empty", "content": ""},
                ]
            }

    [event] = TavilySourceAdapter(client=FakeTavily()).fetch_events("ACME earnings", limit=2)
    assert event.title == "ACME reports growth"
    assert event.content == "Full report content"
    assert event.source == "https://example.test/acme"


def test_event_routing_update_kill_and_ignore_flow(tmp_path):
    repository = JsonRepository(tmp_path / "records.json")
    llm = MockLLMClient()
    events = [
        Event(
            id="evt-1", source="fixture", title="ACME raises guidance",
            content="ACME raises revenue guidance after strong demand.", companies_mentioned=["ACME"],
        ),
        Event(
            id="evt-2", source="fixture", title="ACME expands production",
            content="ACME confirms stronger orders and demand.", companies_mentioned=["ACME"],
        ),
        Event(
            id="evt-3", source="fixture", title="ACME halts orders",
            content="ACME cancels orders and shifts the product line to ASIC.", companies_mentioned=["ACME"],
        ),
        Event(
            id="evt-4", source="fixture", title="ACME CEO makes a donation",
            content="A charity donation to an ethics lab.", companies_mentioned=["ACME"],
        ),
    ]
    pipeline = MarketHypothesisPipeline(
        source=InMemorySourceAdapter(events),
        analysis=AnalysisLayer(llm, repository),
        prediction=PredictionLayer(llm, repository),
        repository=repository,
    )

    generated, updated, killed, ignored = pipeline.run("ACME", limit=4)

    assert generated.decision.action == RouterAction.GENERATE_THESIS
    assert generated.thesis is not None and generated.prediction.version == 1
    assert updated.decision.action == RouterAction.UPDATE_THESIS
    assert updated.thesis is not None and len(updated.thesis.evidence) == 2
    assert updated.prediction is not None and updated.prediction.version == 2
    assert killed.thesis is not None and killed.thesis.status.value == "KILLED"
    assert killed.thesis.kill_reason
    assert killed.prediction is None
    assert repository.get(Prediction, updated.prediction.id).status == PredictionStatus.INVALIDATED
    assert ignored.decision.action == RouterAction.IGNORE
    assert ignored.thesis is None and ignored.prediction is None


def test_prediction_updates_keep_version_history(tmp_path):
    from domain.models.thesis import Thesis

    repository = JsonRepository(tmp_path / "records.json")
    llm = MockLLMClient()
    thesis = Thesis(
        id="thesis-1",
        ticker="ACME",
        core_claim="Demand remains strong.",
        core_assumptions=["Demand persists."],
        strength=0.7,
        reasoning="The event supports the claim.",
    )
    repository.save(thesis)
    layer = PredictionLayer(llm, repository)

    first = layer.generate(thesis)
    second = layer.generate(thesis)

    assert first.version == 1
    assert second.version == 2
    assert repository.get(Prediction, first.id).status == PredictionStatus.SUPERSEDED
    assert len(repository.list(Prediction)) == 2
