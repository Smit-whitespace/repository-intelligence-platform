"""Tests for golden repository benchmarks."""

from eval.benchmarks import BENCHMARKS
from eval.models import RetrievalTestCase


class TestBenchmarks:
    """Tests for the golden benchmark suite."""

    def test_benchmark_count(self) -> None:
        """Should have between 10 and 20 benchmarks."""

        assert 10 <= len(BENCHMARKS) <= 20

    def test_all_benchmarks_are_valid_test_cases(self) -> None:
        """Every benchmark should be a valid RetrievalTestCase."""

        for benchmark in BENCHMARKS:
            assert isinstance(
                benchmark,
                RetrievalTestCase,
            )

    def test_all_have_query(self) -> None:
        """Every benchmark should have a non-empty query."""

        for benchmark in BENCHMARKS:
            assert benchmark.query

    def test_all_have_expected_file_paths(self) -> None:
        """Every benchmark should have at least one expected file."""

        for benchmark in BENCHMARKS:
            assert benchmark.expected_file_paths

    def test_all_expected_files_exist(self) -> None:
        """All expected file paths should exist in the repo."""

        for benchmark in BENCHMARKS:
            for path in benchmark.expected_file_paths:
                assert path, f"Empty path in benchmark: {benchmark.query}"

    def test_all_have_expected_concepts(self) -> None:
        """Every benchmark should have expected concepts."""

        for benchmark in BENCHMARKS:
            assert benchmark.expected_concepts

    def test_coverage_across_subsystems(self) -> None:
        """Benchmarks should cover all major subsystems."""

        all_paths = set()
        for benchmark in BENCHMARKS:
            all_paths.update(
                benchmark.expected_file_paths,
            )

        assert any("initialization_service" in p for p in all_paths), (
            "Missing project initialization coverage"
        )

        assert any(
            "repository/scanner" in p or "repository/service" in p for p in all_paths
        ), "Missing repository scanning coverage"

        assert any(
            "indexing/indexer" in p or "indexing/service" in p for p in all_paths
        ), "Missing indexing coverage"

        assert any("retrieval_service" in p for p in all_paths), (
            "Missing retrieval coverage"
        )

        assert any("context_assembly" in p for p in all_paths), (
            "Missing context assembly coverage"
        )

        assert any("chat/service" in p for p in all_paths), "Missing chat coverage"

        assert any(
            "editing/service" in p or "editing/change_applier" in p for p in all_paths
        ), "Missing editing coverage"

        assert any("core/storage" in p for p in all_paths), "Missing storage coverage"

        assert any("dependencies/providers" in p for p in all_paths), (
            "Missing dependency injection coverage"
        )
