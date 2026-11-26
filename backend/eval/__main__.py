"""Measure semantic search on a real, indexed project.

    cd backend
    python -m eval --root <indexed project root> [--limit 10] [--json report.json]

Runs every benchmark question through the same retrieval service the app
and the MCP server use, with the configured embedding model, and prints
how often the right file comes first, in the top 3, and anywhere in the
results. Open (index) the project in RIP first.
"""

import argparse
import json
from pathlib import Path

from app.dependencies.providers import get_retrieval_service
from eval.benchmarks import BENCHMARKS
from eval.holdout import HOLDOUT
from eval.models import RetrievalEvalReport
from eval.runner import RetrievalEvaluator


def _first_hit_rank(
    mrr: float,
) -> int | None:
    return round(1 / mrr) if mrr else None


def summarize(
    report: RetrievalEvalReport,
) -> dict[str, float]:
    """Hit rates at 1, 3 and the result limit, plus the report's averages."""

    ranks = [
        _first_hit_rank(result.mrr)
        for result in report.results
    ]

    total = max(len(ranks), 1)

    return {
        "cases": len(ranks),
        "hit_at_1": sum(1 for r in ranks if r == 1) / total,
        "hit_at_3": sum(1 for r in ranks if r is not None and r <= 3) / total,
        "hit_at_limit": sum(1 for r in ranks if r is not None) / total,
        "mrr": report.avg_mrr,
        "recall": report.avg_recall,
        "precision": report.avg_precision,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m eval",
        description=__doc__.split("\n\n")[0],
    )

    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Root of a project that RIP has indexed.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Chunks retrieved per question (default 10, as agents get).",
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
        help="Also write the full report, with every retrieved path, here.",
    )

    args = parser.parse_args()

    report = RetrievalEvaluator(
        retrieval_service=get_retrieval_service(),
        root_directory=str(args.root.resolve()),
    ).evaluate(
        HOLDOUT if args.set == "holdout" else BENCHMARKS,
        limit=args.limit,
    )

    for result in report.results:
        rank = _first_hit_rank(result.mrr)

        print(
            f"{'miss' if rank is None else f'#{rank}':>5}  "
            f"recall {result.recall:4.0%}  {result.test_case.query}",
        )

    summary = summarize(report)

    print()
    print(
        f"{summary['cases']} questions, top {args.limit} chunks: "
        f"hit@1 {summary['hit_at_1']:.0%}, hit@3 {summary['hit_at_3']:.0%}, "
        f"hit@{args.limit} {summary['hit_at_limit']:.0%}, "
        f"MRR {summary['mrr']:.2f}, recall {summary['recall']:.0%}",
    )

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "summary": summary,
                    "report": report.model_dump(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
