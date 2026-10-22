import json
from pathlib import Path

_DIR = Path(__file__).parent


def render_prompt(name: str, context: dict, extra: str = "") -> str:
    """Prompt template + CONTEXT_JSON payload (the marker the mock LLM also parses)."""
    text = (_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()
    return f"{text}{extra}\nCONTEXT_JSON\n{json.dumps(context, ensure_ascii=False, default=str)}"
