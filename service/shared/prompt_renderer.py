from pathlib import Path
from typing import Any

class PromptRenderer:
    """
    Role: Prompt Engineer & Template Manager.
    Nhận dữ liệu thô (từ WebTool) và nhét vào template (.txt) 
    để tạo ra câu lệnh hoàn chỉnh trước khi bắn lên OpenAI.
    """

    _DOMAIN_PATH = Path(__file__).parent.parent.parent / "domain" / "prompts"
    _RESEARCH_PROMPT = _DOMAIN_PATH / "research.txt"
    _ANALYSE_PROMPT = _DOMAIN_PATH / "analyse.txt"

    @staticmethod
    def _render_prompt(template: str, **context: Any) -> str:
        """Render the prompt template with the provided context."""
        try:
            return template.format(**context)
        except KeyError as exc:
            missing_key = exc.args[0]
            raise ValueError(
                f"Missing prompt context variable: '{missing_key}'"
            ) from exc

    def research_prompt(self, **context: Any) -> str:
        """
        Injects fetched news data into the Research template.
        Expected context keys: 'fetched_data', 'max_theses'
        """
        template = self._RESEARCH_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)

    def analyse_prompt(self, **context: Any) -> str:
        """
        Injects hypotheses and specific evidence into the Analyse template.
        Expected context keys: 'event_context', 'thinking_process', 'evidence'
        """
        template = self._ANALYSE_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)