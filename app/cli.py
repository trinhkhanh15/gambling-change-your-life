import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv

from domain.models.session import Thesis
from service.pipelines.orchestration import Orchestrator


def load_env_file() -> None:
	env_path = Path(__file__).resolve().parents[1] / ".env"
	load_dotenv(dotenv_path=env_path, override=False)


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Generate and analyse market theses from recent news."
	)
	parser.add_argument(
		"--max-results",
		type=int,
		default=3,
		help="Maximum number of theses to generate (default: 3).",
	)
	return parser


def format_thesis(index: int, thesis: Thesis) -> str:
	evidence = "\n".join(f"- {item}" for item in (thesis.evidence or []))
	counter_evidence = "\n".join(
		f"- {item}" for item in (thesis.counter_evidence or [])
	)
	return "\n".join(
		[
			f"## Thesis {index}",
			f"**What happened:** {thesis.content}",
			f"**Reasoning:** {thesis.thinking}",
			f"**Prediction:** {thesis.prediction}",
			f"**Confidence:** {thesis.confidence:.2f}",
			"**Evidence:**",
			evidence or "- None provided",
			"**Counter-evidence:**",
			counter_evidence or "- None provided",
			"**Created at:** {thesis.created_at.isoformat()}",
		]
	)


def main(argv: Sequence[str] | None = None) -> int:
	args = build_parser().parse_args(argv)
	load_env_file()

	if args.max_results < 1:
		print("error: --max-results must be at least 1", file=sys.stderr)
		return 2

	api_key = os.environ.get("OPENAI_API_KEY")
	if not api_key:
		print("error: set OPENAI_API_KEY before running the app", file=sys.stderr)
		return 2

	try:
		theses = Orchestrator(openai_api_key=api_key).execute(max_results=args.max_results)
	except Exception as exc:
		print(f"error: {exc}", file=sys.stderr)
		return 1

	if not theses:
		print("No theses were generated.")
		return 0

	print("\n\n".join(format_thesis(index, thesis) for index, thesis in enumerate(theses, 1)))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
