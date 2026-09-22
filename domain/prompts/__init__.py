from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")