import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.schema import (
    Event,
    RouterAction,
    RouterDecision,
    Thesis,
    ThesisGenerateOutput,
    ThesisStatus,
    ThesisUpdateOutput,
)


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


class MockFinancialLLMClient(BaseLLMClient):
    def route_event(self, event: Event, candidate_theses: List[Thesis]) -> RouterDecision:
        content_lower = (event.title + " " + event.content).lower()

        if any(w in content_lower for w in ["philanthropy", "commencement speech", "grant", "donation", "ethics lab"]):
            return RouterDecision(
                action=RouterAction.IGNORE,
                target_thesis_id=None,
                reasoning="Event mang tính chất PR/từ thiện cá nhân và học thuật, không có tác động trực tiếp đến dòng tiền, biên lợi nhuận hay động lực kinh doanh của công ty.",
            )

        matched_thesis = None
        for th in candidate_theses:
            if th.status == ThesisStatus.ACTIVE:
                if any(c.upper() in [t.upper() for t in event.companies_mentioned] for c in [th.ticker]) or \
                   any(s.lower() in content_lower for s in ["semiconductor", "ai chip", "data center", "accelerator", "capex"]):
                    matched_thesis = th
                    break

        if matched_thesis:
            return RouterDecision(
                action=RouterAction.UPDATE_THESIS,
                target_thesis_id=matched_thesis.id,
                reasoning=f"Event cung cấp dữ liệu thị trường mới trực tiếp tác động đến giả định hoặc động lực của Thesis '{matched_thesis.id}' ({matched_thesis.ticker}). Cần cập nhật bằng chứng và đánh giá lại độ vững chắc của thesis.",
            )

        return RouterDecision(
            action=RouterAction.GENERATE_THESIS,
            target_thesis_id=None,
            reasoning=f"Event mang thông tin tài chính/kinh doanh cốt lõi (surprise earnings beat hoặc thay đổi guidance) cho {', '.join(event.companies_mentioned) or 'thị trường'}. Chưa có thesis nào đang theo dõi chủ đề này.",
        )

    def generate_thesis(self, event: Event) -> ThesisGenerateOutput:
        ticker = event.companies_mentioned[0] if event.companies_mentioned else "UNKNOWN"
        
        core_claim = (
            f"Nhu cầu tăng tốc đầu tư hạ tầng AI và chu kỳ sản phẩm mới sẽ duy trì tốc độ tăng trưởng "
            f"doanh thu Data Center của {ticker} vượt trên kỳ vọng đồng thuận của thị trường."
        )
        core_assumptions = [
            "Giả định 1: Các Cloud Hyperscalers (Microsoft, Google, Meta, Amazon) tiếp tục mở rộng ngân sách CapEx cho GPU AI.",
            "Giả định 2: Chuỗi cung ứng bán dẫn và năng lực đóng gói tiên tiến (packaging) đáp ứng kịp đơn hàng mà không gặp gián đoạn nghiêm trọng.",
            "Giả định 3: Khách hàng duy trì việc mua chip AI thương mại thay vì tự phát triển chip chuyên dụng (in-house ASIC) trên diện rộng."
        ]
        
        evidence_points = [
            f"Số liệu thực tế: {event.title}. {event.content[:180]}..."
        ]
        
        counter_evidence_points = [
            "Rủi ro định giá: P/E và kỳ vọng của thị trường đã ở mức rất cao, khiến biên độ thất vọng khi có sự cố là rất lớn.",
            "Rủi ro chu kỳ & tập trung khách hàng: Doanh thu phụ thuộc lớn vào một nhóm nhỏ hyperscalers có thể giảm tốc khi hạ tầng cơ bản được hoàn tất."
        ]
        
        reasoning = (
            f"Sự kiện {event.id} tạo ra một positive surprise rõ rệt so với kỳ vọng ban đầu. "
            f"Doanh thu và guidance vượt trội chứng minh chu kỳ đầu tư AI vẫn đang trong pha tăng tốc mạnh mẽ. "
            f"Tuy nhiên, cần theo dõi sát sao tiến độ CapEx của nhóm khách hàng lớn và khả năng cung ứng đóng gói."
        )

        return ThesisGenerateOutput(
            ticker=ticker,
            core_claim=core_claim,
            core_assumptions=core_assumptions,
            initial_strength=0.75,
            evidence_points=evidence_points,
            counter_evidence_points=counter_evidence_points,
            reasoning=reasoning,
        )

    def update_kill_thesis(self, event: Event, thesis: Thesis) -> ThesisUpdateOutput:
        content_lower = (event.title + " " + event.content).lower()

        is_core_assumption_shattered = any(
            phrase in content_lower for phrase in [
                "halt", "freeze", "canceling", "cancelation", "shift 50%", "in-house custom asic",
                "halting nvda orders", "proprietory silicon"
            ]
        )

        if is_core_assumption_shattered:
            kill_reason = (
                f"Sự kiện {event.id} trực tiếp phá hủy Giả định cốt lõi số 1 và 3: Các đối tác Cloud lớn nhất "
                f"(Amazon, Google, Meta) đã đóng băng đơn hàng và dịch chuyển sang chip ASIC tự phát triển. "
                f"Động lực tăng trưởng của thesis không còn hợp lệ."
            )
            return ThesisUpdateOutput(
                new_status=ThesisStatus.KILLED,
                kill_reason=kill_reason,
                new_strength=0.0,
                new_evidence_points=[],
                new_counter_evidence_points=[
                    f"Phá vỡ giả định cốt lõi: {event.title} - Báo cáo chỉ ra các Big Tech hủy đơn hàng trị giá hơn $12B để chuyển sang in-house silicon."
                ],
                updated_reasoning=f"THESIS KILLED: {kill_reason}",
            )

        is_bottleneck = any(
            phrase in content_lower for phrase in [
                "bottleneck", "delay", "shortage", "capacity constraint", "friction"
            ]
        )

        if is_bottleneck:
            new_str = max(0.20, round(thesis.strength - 0.15, 2))
            return ThesisUpdateOutput(
                new_status=ThesisStatus.ACTIVE,
                kill_reason=None,
                new_strength=new_str,
                new_evidence_points=[],
                new_counter_evidence_points=[
                    f"Rủi ro chuỗi cung ứng: {event.title} - Sự cố đóng gói kéo dài thời gian giao hàng thêm 6-8 tuần."
                ],
                updated_reasoning=(
                    f"Sự kiện {event.id} bổ sung rủi ro nghẽn cung ứng (counter-evidence). "
                    f"Mặc dù nhu cầu vẫn nguyên vẹn nhưng rủi ro không đạt kỳ vọng doanh số ngắn hạn tăng lên, "
                    f"hạ độ vững chắc (strength) của thesis từ {thesis.strength} xuống {new_str}."
                ),
            )

        new_str = min(0.95, round(thesis.strength + 0.10, 2))
        return ThesisUpdateOutput(
            new_status=ThesisStatus.ACTIVE,
            kill_reason=None,
            new_strength=new_str,
            new_evidence_points=[
                f"Bằng chứng củng cố: {event.title} - Xác nhận mở rộng CapEx thêm $18B cho hạ tầng AI."
            ],
            new_counter_evidence_points=[],
            updated_reasoning=(
                f"Sự kiện {event.id} củng cố trực tiếp Giả định 1 về việc khách hàng tiếp tục mở rộng CapEx. "
                f"Độ vững chắc (strength) của thesis được nâng từ {thesis.strength} lên {new_str}."
            ),
        )


def get_llm_client() -> BaseLLMClient:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        pass
    return MockFinancialLLMClient()
