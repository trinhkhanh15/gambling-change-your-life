from pathlib import Path
from typing import Any


class PromptRenderer:
    _DOMAIN_PATH = Path(__file__).parent.parent.parent / "domain" / "prompts"

    _RESEARCH_PROMPT = _DOMAIN_PATH / "research.txt"
    _ANALYSE_PROMPT = _DOMAIN_PATH / "analyse.txt"
    _ROUTER_PROMPT = _DOMAIN_PATH / "router.txt"
    _GENERATE_THESIS_PROMPT = _DOMAIN_PATH / "generate_thesis.txt"
    _UPDATE_KILL_THESIS_PROMPT = _DOMAIN_PATH / "update_kill_thesis.txt"
    _DECOMPOSE_EVENT_PROMPT = _DOMAIN_PATH / "decompose_event.txt"

    @staticmethod
    def _render_prompt(template: str, **context: Any) -> str:
        try:
            return template.format(**context)
        except KeyError as exc:
            missing_key = exc.args[0]
            raise ValueError(
                f"Missing prompt context variable: '{missing_key}'"
            ) from exc

    def research_prompt(self, **context: Any) -> str:
        template = self._RESEARCH_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)

    def analyse_prompt(self, **context: Any) -> str:
        template = self._ANALYSE_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)

    def router_prompt(self, **context: Any) -> str:
        template = self._ROUTER_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)

    def generate_thesis_prompt(self, **context: Any) -> str:
        template = self._GENERATE_THESIS_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)

    def update_kill_thesis_prompt(self, **context: Any) -> str:
        template = self._UPDATE_KILL_THESIS_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)

    def decompose_event_prompt(self, **context: Any) -> str:
        template = self._DECOMPOSE_EVENT_PROMPT.read_text(encoding="utf-8")
        return self._render_prompt(template, **context)