"""Measure chat answers on a real, indexed project.

    cd backend
    python -m eval.answers --root <indexed project root> [--set tuning|holdout]
        [--json report.json]

Asks every question through the same chat service the app uses, with the
configured chat model, and scores each answer: how many of the expected
files it cites, symbols it names and concepts it explains, and how many
file paths or names it mentions that do not exist in the project. The
model answers differently each run, so compare prompt versions over more
than one run. Open (index) the project in RIP first; Ollama must be
running.
"""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.dependencies.providers import get_chat_service
from app.dependencies.providers import get_model_resolver
from app.llm.config import Task
from eval.answer_quality import evaluate_answers
from eval.answer_quality import load_repository
from eval.answer_quality import summarize_scores
from eval.benchmarks import BENCHMARKS
from eval.holdout import HOLDOUT


def _percent(
    value: float | None,
) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m eval.answers",
        description=__doc__.split("\n\n")[0],
    )

    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Root of a project that RIP has indexed.",
    )

    parser.add_argument(
        "--set",
        choices=["tuning", "holdout"],
        default="tuning",
        help="Which questions: the tuning set, or the held-out set never used for tuning.",
    )

    parser.add_argument(
        "--json",
        type=Path,
        help="Also write every answer and its score here.",
    )

    args = parser.parse_args()

    root = args.root.resolve()

    model = get_model_resolver().for_task(Task.CHAT_ANSWER)

    print(f"Model: {model.provider}/{model.model}")

    scores = evaluate_answers(
        get_chat_service(),
        HOLDOUT if args.set == "holdout" else BENCHMARKS,
        root,
        load_repository(root),
    )

    for score in scores:
        flags = []

        if score.refused:
            flags.append("refused")

        if score.invented:
            flags.append(
                "invented: "
                + ", ".join(score.invented_paths + score.invented_identifiers),
            )

        print(
            f"{score.coverage:4.0%}  {score.words:4d} words  "
            f"{score.seconds:5.1f}s  {score.query}"
            + (f"  [{'; '.join(flags)}]" if flags else ""),
        )

    summary = summarize_scores(scores)

    print()
    print(
        f"{summary['answers']} answers: coverage {_percent(summary['coverage'])} "
        f"(files {_percent(summary['file_coverage'])}, "
        f"symbols {_percent(summary['symbol_coverage'])}, "
        f"concepts {_percent(summary['concept_coverage'])}), "
        f"invented names in {_percent(summary['answers_with_invented_names'])} "
        f"of answers, refusals {_percent(summary['refusals'])}, "
        f"{summary['words']:.0f} words, {summary['seconds']:.1f}s each",
    )

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "model": f"{model.provider}/{model.model}",
                    "summary": summary,
                    "answers": [asdict(score) for score in scores],
                },
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
