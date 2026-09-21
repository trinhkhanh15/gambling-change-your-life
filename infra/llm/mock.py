from __future__ import annotations

import re
from typing import Any, Optional, Type, Union
from pydantic import BaseModel

from domain.schema.event import DecomposedEventItem, EventDecompositionOutput, EventNature, EventScope
from domain.schema.router import (
    RouterAction,
    RouterDecision,
    ThesisGenerateOutput,
    ThesisUpdateOutput,
)
from domain.schema.thesis import ThesisStatus


class MockLLMClient:
    def generate_response(
        self,
        system_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> Union[str, Any]:
        if response_model is None:
            return f"Mock response for prompt of length {len(system_prompt)}"

        event_text = ""
        if "### Incoming Event:" in system_prompt:
            event_part = system_prompt.split("### Incoming Event:", 1)[1]
            if "###" in event_part:
                event_text = event_part.split("###", 1)[0].lower()
            else:
                event_text = event_part.lower()
        else:
            event_text = system_prompt.lower()

        if response_model == RouterDecision:
            if any(
                w in event_text
                for w in ["commencement speech", "grant", "donation", "ethics lab", "philanthropy", "pledges $5m", "charity"]
            ):
                return RouterDecision(
                    action=RouterAction.IGNORE,
                    target_thesis_id=None,
                    reasoning="Event mang tính chất PR/từ thiện cá nhân và học thuật, không có tác động trực tiếp đến dòng tiền, biên lợi nhuận hay động lực kinh doanh của công ty.",
                )

            candidate_section = ""
            if "### Candidate Theses" in system_prompt:
                cand_part = system_prompt.split("### Candidate Theses", 1)[1]
                if "###" in cand_part:
                    candidate_section = cand_part.split("###", 1)[0]
                else:
                    candidate_section = cand_part

            thesis_match = re.search(r"THESIS-[A-Z0-9]+-\d+", candidate_section)
            has_semiconductor_keywords = any(
                s in event_text
                for s in ["semiconductor", "ai chip", "data center", "accelerator", "capex", "nvda", "packaging", "bottleneck", "tsmc", "asic"]
            )

            if thesis_match and has_semiconductor_keywords:
                matched_id = thesis_match.group(0)
                return RouterDecision(
                    action=RouterAction.UPDATE_THESIS,
                    target_thesis_id=matched_id,
                    reasoning=f"Event cung cấp dữ liệu thị trường mới trực tiếp tác động đến giả định hoặc động lực của Thesis '{matched_id}'. Cần cập nhật bằng chứng và đánh giá lại độ vững chắc của thesis.",
                )

            return RouterDecision(
                action=RouterAction.GENERATE_THESIS,
                target_thesis_id=None,
                reasoning="Event mang thông tin tài chính/kinh doanh cốt lõi (surprise earnings beat hoặc thay đổi guidance). Chưa có thesis nào đang theo dõi chủ đề này.",
            )

        if response_model == ThesisGenerateOutput:
            ticker_match = re.search(r"Companies:\s*([A-Z0-9]+)", system_prompt)
            ticker = ticker_match.group(1) if ticker_match else "NVDA"

            title_match = re.search(r"- Title:\s*(.+)", system_prompt)
            title = title_match.group(1).strip() if title_match else "Financial event"

            content_match = re.search(r"- Content:\s*(.+)", system_prompt)
            content = content_match.group(1).strip() if content_match else ""

            return ThesisGenerateOutput(
                ticker=ticker,
                core_claim=f"Nhu cầu tăng tốc đầu tư hạ tầng AI và chu kỳ sản phẩm mới sẽ duy trì tốc độ tăng trưởng doanh thu Data Center của {ticker} vượt trên kỳ vọng đồng thuận của thị trường.",
                core_assumptions=[
                    "Giả định 1: Các Cloud Hyperscalers (Microsoft, Google, Meta, Amazon) tiếp tục mở rộng ngân sách CapEx cho GPU AI.",
                    "Giả định 2: Chuỗi cung ứng bán dẫn và năng lực đóng gói tiên tiến (packaging) đáp ứng kịp đơn hàng mà không gặp gián đoạn nghiêm trọng.",
                    "Giả định 3: Khách hàng duy trì việc mua chip AI thương mại thay vì tự phát triển chip chuyên dụng (in-house ASIC) trên diện rộng.",
                ],
                initial_strength=0.75,
                evidence_points=[
                    f"Số liệu thực tế: {title}. {content[:180]}...",
                ],
                counter_evidence_points=[
                    "Rủi ro định giá: P/E và kỳ vọng của thị trường đã ở mức rất cao, khiến biên độ thất vọng khi có sự cố là rất lớn.",
                    "Rủi ro chu kỳ & tập trung khách hàng: Doanh thu phụ thuộc lớn vào một nhóm nhỏ hyperscalers có thể giảm tốc khi hạ tầng cơ bản được hoàn tất.",
                ],
                reasoning="Sự kiện tạo ra một positive surprise rõ rệt so với kỳ vọng ban đầu. Doanh thu và guidance vượt trội chứng minh chu kỳ đầu tư AI vẫn đang trong pha tăng tốc mạnh mẽ.",
            )

        if response_model == ThesisUpdateOutput:
            title_match = re.search(r"- Title:\s*(.+)", system_prompt)
            title = title_match.group(1).strip() if title_match else "Financial event"

            is_core_assumption_shattered = any(
                phrase in event_text
                for phrase in [
                    "halt", "freeze", "canceling", "cancelation", "shift 50%", "in-house custom asic",
                    "halting nvda orders", "proprietory silicon"
                ]
            )

            if is_core_assumption_shattered:
                kill_reason = "Sự kiện trực tiếp phá hủy Giả định cốt lõi số 1 và 3: Các đối tác Cloud lớn nhất đã đóng băng đơn hàng và dịch chuyển sang chip ASIC tự phát triển. Động lực tăng trưởng của thesis không còn hợp lệ."
                return ThesisUpdateOutput(
                    new_status=ThesisStatus.KILLED,
                    kill_reason=kill_reason,
                    new_strength=0.0,
                    new_evidence_points=[],
                    new_counter_evidence_points=[
                        f"Phá vỡ giả định cốt lõi: {title} - Báo cáo chỉ ra các Big Tech hủy đơn hàng trị giá hơn $12B để chuyển sang in-house silicon.",
                    ],
                    updated_reasoning=f"THESIS KILLED: {kill_reason}",
                )

            is_bottleneck = any(
                phrase in event_text
                for phrase in ["bottleneck", "delay", "shortage", "capacity constraint", "friction"]
            )

            strength_match = re.search(r"Current Strength:\s*([0-9.]+)", system_prompt)
            current_strength = float(strength_match.group(1)) if strength_match else 0.75

            if is_bottleneck:
                new_str = max(0.20, round(current_strength - 0.15, 2))
                return ThesisUpdateOutput(
                    new_status=ThesisStatus.ACTIVE,
                    kill_reason=None,
                    new_strength=new_str,
                    new_evidence_points=[],
                    new_counter_evidence_points=[
                        f"Rủi ro chuỗi cung ứng: {title} - Sự cố đóng gói kéo dài thời gian giao hàng thêm 6-8 tuần.",
                    ],
                    updated_reasoning=f"Sự kiện bổ sung rủi ro nghẽn cung ứng (counter-evidence), hạ độ vững chắc từ {current_strength} xuống {new_str}.",
                )

            new_str = min(0.95, round(current_strength + 0.10, 2))
            return ThesisUpdateOutput(
                new_status=ThesisStatus.ACTIVE,
                kill_reason=None,
                new_strength=new_str,
                new_evidence_points=[
                    f"Bằng chứng củng cố: {title} - Xác nhận mở rộng CapEx thêm $18B cho hạ tầng AI.",
                ],
                new_counter_evidence_points=[],
                updated_reasoning=f"Sự kiện củng cố trực tiếp Giả định 1 về việc khách hàng tiếp tục mở rộng CapEx. Độ vững chắc được nâng từ {current_strength} lên {new_str}.",
            )

        if response_model == EventDecompositionOutput:
            title_match = re.search(r"Title:\s*(.+)", system_prompt)
            title = title_match.group(1).strip() if title_match else "News event"
            content_match = re.search(r"Content:\s*(.+)", system_prompt)
            content = content_match.group(1).strip() if content_match else ""
            return EventDecompositionOutput(
                events=[
                    DecomposedEventItem(
                        title=title,
                        content=content,
                        nature=EventNature.FACT,
                        scope=EventScope.COMPANY,
                    )
                ]
            )

        return response_model()
