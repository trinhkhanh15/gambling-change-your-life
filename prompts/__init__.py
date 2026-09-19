from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "domain" / "prompts"
ROUTER_PROMPT_PATH = PROMPTS_DIR / "router.txt"
GENERATE_THESIS_PROMPT_PATH = PROMPTS_DIR / "generate_thesis.txt"
UPDATE_KILL_THESIS_PROMPT_PATH = PROMPTS_DIR / "update_kill_thesis.txt"

__all__ = [
    "PROMPTS_DIR",
    "ROUTER_PROMPT_PATH",
    "GENERATE_THESIS_PROMPT_PATH",
    "UPDATE_KILL_THESIS_PROMPT_PATH",
]
