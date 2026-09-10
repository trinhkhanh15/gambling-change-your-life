import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import AnalysisPipeline
from src.schema import Event, RouterAction, ThesisStatus


def run_dod_verification():
    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU CHẠY KIỂM THỬ DEFINITION OF DONE (DoD) - ANALYSIS LAYER")
    print("=" * 80 + "\n")

    events_path = project_root / "tests" / "sample_events.json"
    with open(events_path, "r", encoding="utf-8") as f:
        raw_events = json.load(f)

    pipeline = AnalysisPipeline()

    for idx, raw_evt in enumerate(raw_events, 1):
        event = Event(**raw_evt)
        print(f"\n[{idx}/5] -------------------------------------------------------------")
        print(f"📥 EVENT INTAKE: [{event.id}] - {event.title}")
        print(f"   Source: {event.source} | Nature: {event.nature.value} | Scope: {event.scope.value}")
        if event.expectation_context:
            print(f"   Consensus: {event.expectation_context.consensus_metric} "
                  f"(Expected: {event.expectation_context.expected_value} vs Actual: {event.expectation_context.actual_value}) "
                  f"-> [{event.expectation_context.surprise_direction}]")

        decision, result_thesis = pipeline.process_event(event)

        print(f"\n👉 ROUTER DECISION: {decision.action.value}")
        print(f"   Reasoning: {decision.reasoning}")

        if decision.action == RouterAction.GENERATE_THESIS:
            assert result_thesis is not None, "Thesis phải được tạo khi action là GENERATE_THESIS"
            assert result_thesis.status == ThesisStatus.ACTIVE
            assert result_thesis.strength > 0.5
            assert len(result_thesis.core_assumptions) >= 2
            assert len(result_thesis.counter_evidence) >= 1
            print(f"\n   ✅ THESIS CREATED: [{result_thesis.id}] ({result_thesis.ticker})")
            print(f"   Core Claim (Immutable): {result_thesis.core_claim}")
            print(f"   Strength: {result_thesis.strength}")
            print(f"   Status: {result_thesis.status.value}")
            print(f"   Core Assumptions:")
            for a in result_thesis.core_assumptions:
                print(f"     - {a}")
            print(f"   Counter-Evidence:")
            for ce in result_thesis.counter_evidence:
                print(f"     - [{ce.event_id}] {ce.point}")

        elif decision.action == RouterAction.UPDATE_THESIS:
            assert result_thesis is not None, "Thesis phải tồn tại khi action là UPDATE_THESIS"
            print(f"\n   🔄 THESIS UPDATED: [{result_thesis.id}] ({result_thesis.ticker})")
            print(f"   New Status: {result_thesis.status.value}")
            print(f"   New Strength: {result_thesis.strength}")
            print(f"   Total Evidence items: {len(result_thesis.evidence)}")
            print(f"   Total Counter-Evidence items: {len(result_thesis.counter_evidence)}")
            print(f"   Updated Reasoning: {result_thesis.reasoning}")

            if result_thesis.status == ThesisStatus.KILLED:
                assert result_thesis.kill_reason is not None, "Killed thesis phải có kill_reason tường minh"
                assert result_thesis.strength == 0.0, "Killed thesis phải có strength == 0"
                print(f"   ❌ KILL REASON: {result_thesis.kill_reason}")

        elif decision.action == RouterAction.IGNORE:
            assert result_thesis is None, "Không có thesis nào được tạo hoặc cập nhật khi action là IGNORE"
            print(f"   ⏭️ EVENT IGNORED: Tin tức không ảnh hưởng đến luận điểm tài chính.")

    print("\n" + "=" * 80)
    print("📊 BÁO CÁO TỔNG KẾT TRẠNG THÁI CUỐI CÙNG")
    print("=" * 80)
    active_theses = pipeline.get_active_theses()
    killed_theses = pipeline.get_killed_theses()

    print(f"Tổng số Active Theses : {len(active_theses)}")
    print(f"Tổng số Killed Theses : {len(killed_theses)}")

    assert len(killed_theses) == 1, "Kỳ vọng đúng 1 thesis bị KILL (sau Event 4)"
    assert killed_theses[0].id == "THESIS-NVDA-001"
    assert killed_theses[0].status == ThesisStatus.KILLED
    assert killed_theses[0].kill_reason is not None

    print("\n🎉 KIỂM THỬ THÀNH CÔNG! HỆ THỐNG ĐÃ ĐẠT TOÀN BỘ TIÊU CHÍ DEFINITION OF DONE (DoD)!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_dod_verification()
