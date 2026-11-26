"""Tests for retrieval evaluation runner."""

from pathlib import Path
from unittest.mock import MagicMock

from app.indexing.retrieval_models import (
    SearchResult,
)
from app.indexing.retrieval_service import (
    RetrievalService,
)
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryChunkMetadata,
)
from eval.models import (
    RetrievalTestCase,
)
from eval.runner import (
    RetrievalEvaluator,
    create_retrieval_evaluator,
)


def create_result(
    relative_path: str = "main.py",
    score: float = 0.8,
) -> SearchResult:
    """Create a sample search result."""

    return SearchResult(
        chunk_id="chunk-1",
        content="def foo(): pass",
        metadata=RepositoryChunkMetadata(
            relative_path=Path(relative_path),
            language="python",
            mime_type="text/x-python",
            sha256="abc",
        ),
        boundary=ChunkBoundary(
            start_line=1,
            end_line=2,
            chunk_type=ChunkType.FUNCTION,
        ),
        similarity_score=score,
    )


class TestRetrievalEvaluator:
    """Tests for RetrievalEvaluator."""

    def test_windows_paths_match_forward_slash_expectations(self) -> None:
        """Indexes built on Windows store backslash paths; benchmarks are
        written with forward slashes. Every case used to score zero."""

        service = MagicMock(
            spec=RetrievalService,
        )

        service.search.return_value = MagicMock(
            results=[
                create_result(
                    relative_path="backend\\app\\chat\\service.py",
                ),
            ],
        )

        report = RetrievalEvaluator(
            retrieval_service=service,
        ).evaluate(
            test_cases=[
                RetrievalTestCase(
                    query="How does chat work?",
                    expected_file_paths=["backend/app/chat/service.py"],
                ),
            ],
        )

        assert report.results[0].retrieved_file_paths == [
            "backend/app/chat/service.py",
        ]

        assert report.avg_mrr == 1.0

    def test_all_results_relevant(self) -> None:
        """Perfect precision and recall when all results match."""

        service = MagicMock(
            spec=RetrievalService,
        )

        service.search.return_value = MagicMock(
            results=[
                create_result(
                    relative_path="main.py",
                ),
            ],
        )

        evaluator = RetrievalEvaluator(
            retrieval_service=service,
        )

        report = evaluator.evaluate(
            test_cases=[
                RetrievalTestCase(
                    query="find main",
                    expected_file_paths=["main.py"],
                ),
            ],
        )

        assert report.total_cases == 1

        assert report.avg_precision == 1.0

        assert report.avg_recall == 1.0

        assert report.avg_f1 == 1.0

        assert report.avg_mrr == 1.0

    def test_no_relevant_results(self) -> None:
        """Zero precision and recall when no results match."""

        service = MagicMock(
            spec=RetrievalService,
        )

        service.search.return_value = MagicMock(
            results=[
                create_result(
                    relative_path="other.py",
                ),
            ],
        )

        evaluator = RetrievalEvaluator(
            retrieval_service=service,
        )

        report = evaluator.evaluate(
            test_cases=[
                RetrievalTestCase(
                    query="find main",
                    expected_file_paths=["main.py"],
                ),
            ],
        )

        assert report.avg_precision == 0.0

        assert report.avg_recall == 0.0

        assert report.avg_f1 == 0.0

        assert report.avg_mrr == 0.0

    def test_partial_match(self) -> None:
        """Partial match produces intermediate scores."""

        service = MagicMock(
            spec=RetrievalService,
        )

        service.search.return_value = MagicMock(
            results=[
                create_result(
                    relative_path="main.py",
                ),
                create_result(
                    relative_path="utils.py",
                ),
            ],
        )

        evaluator = RetrievalEvaluator(
            retrieval_service=service,
        )

        report = evaluator.evaluate(
            test_cases=[
                RetrievalTestCase(
                    query="find main",
                    expected_file_paths=["main.py"],
                ),
            ],
        )

        assert report.avg_precision == 0.5

        assert report.avg_recall == 1.0

    def test_multiple_cases_averaged(self) -> None:
        """Multiple test cases should average their metrics."""

        service = MagicMock(
            spec=RetrievalService,
        )

        def side_effect(
            query,
        ):
            if query.query == "good":
                return MagicMock(
                    results=[
                        create_result(
                            relative_path="main.py",
                        ),
                    ],
                )

            return MagicMock(
                results=[
                    create_result(
                        relative_path="other.py",
                    ),
                ],
            )

        service.search.side_effect = side_effect

        evaluator = RetrievalEvaluator(
            retrieval_service=service,
        )

        report = evaluator.evaluate(
            test_cases=[
                RetrievalTestCase(
                    query="good",
                    expected_file_paths=["main.py"],
                ),
                RetrievalTestCase(
                    query="bad",
                    expected_file_paths=["main.py"],
                ),
            ],
        )

        assert report.total_cases == 2

        assert report.avg_precision == 0.5

        assert report.avg_recall == 0.5

    def test_empty_test_cases(self) -> None:
        """No test cases returns empty report."""

        service = MagicMock(
            spec=RetrievalService,
        )

        evaluator = RetrievalEvaluator(
            retrieval_service=service,
        )

        report = evaluator.evaluate(
            test_cases=[],
        )

        assert report.total_cases == 0

        assert report.avg_precision == 0.0

    def test_passes_limit_to_search(self) -> None:
        """The limit parameter should be forwarded to search."""

        service = MagicMock(
            spec=RetrievalService,
        )

        service.search.return_value = MagicMock(
            results=[],
        )

        evaluator = RetrievalEvaluator(
            retrieval_service=service,
        )

        evaluator.evaluate(
            test_cases=[
                RetrievalTestCase(
                    query="test",
                    expected_file_paths=[],
                ),
            ],
            limit=5,
        )

        assert service.search.call_args[0][0].limit == 5

    def test_mrr_second_position(self) -> None:
        """MRR is 0.5 when first relevant is second result."""

        service = MagicMock(
            spec=RetrievalService,
        )

        service.search.return_value = MagicMock(
            results=[
                create_result(
                    relative_path="a.py",
                ),
                create_result(
                    relative_path="b.py",
                ),
            ],
        )

        evaluator = RetrievalEvaluator(
            retrieval_service=service,
        )

        report = evaluator.evaluate(
            test_cases=[
                RetrievalTestCase(
                    query="find b",
                    expected_file_paths=["b.py"],
                ),
            ],
        )

        assert report.results[0].mrr == 0.5


class TestSummary:
    """The hit rates printed by `python -m eval`."""

    def test_hit_rates_follow_the_rank_of_the_first_right_file(self) -> None:
        from eval.__main__ import summarize

        service = MagicMock(
            spec=RetrievalService,
        )

        # First case: right file first. Second: third. Third: missing.
        service.search.side_effect = [
            MagicMock(results=[create_result("a.py")]),
            MagicMock(
                results=[
                    create_result("x.py"),
                    create_result("y.py"),
                    create_result("b.py"),
                ],
            ),
            MagicMock(results=[create_result("x.py")]),
        ]

        report = RetrievalEvaluator(
            retrieval_service=service,
        ).evaluate(
            [
                RetrievalTestCase(query="a", expected_file_paths=["a.py"]),
                RetrievalTestCase(query="b", expected_file_paths=["b.py"]),
                RetrievalTestCase(query="c", expected_file_paths=["c.py"]),
            ],
        )

        summary = summarize(report)

        assert summary["hit_at_1"] == 1 / 3

        assert summary["hit_at_3"] == 2 / 3

        assert summary["hit_at_limit"] == 2 / 3


class TestCommandLine:
    """`python -m eval` argument checks."""

    def test_a_limit_below_one_is_refused(self) -> None:
        """--limit 0 used to report dozens of results (Graphify, #10)."""

        import pytest

        from eval.__main__ import positive_int

        for bad in ["0", "-3", "abc"]:
            with pytest.raises(Exception):
                positive_int(bad)

        assert positive_int("10") == 10


class TestCreateEvaluator:
    """Tests for create_retrieval_evaluator factory."""

    def test_creates_evaluator(
        self,
    ) -> None:
        """Factory should create a working evaluator."""

        provider = MagicMock()

        store = MagicMock()

        evaluator = create_retrieval_evaluator(
            embedding_provider=provider,
            vector_store=store,
        )

        assert evaluator is not None

        assert isinstance(
            evaluator,
            RetrievalEvaluator,
        )
