"""Tests for evaluation metrics."""

from eval.metrics import (
    f1_score,
    precision,
    recall,
    reciprocal_rank,
)


class TestPrecision:
    """Tests for precision metric."""

    def test_all_relevant(self) -> None:
        """All retrieved items are relevant."""

        assert precision({"a.py"}, {"a.py"}) == 1.0

    def test_none_relevant(self) -> None:
        """No retrieved items are relevant."""

        assert precision({"a.py"}, {"b.py"}) == 0.0

    def test_partial_relevant(self) -> None:
        """Some retrieved items are relevant."""

        result = precision(
            {"a.py", "b.py"},
            {"a.py"},
        )

        assert result == 0.5

    def test_empty_retrieved(self) -> None:
        """No items retrieved yields 0.0."""

        assert precision(set(), {"a.py"}) == 0.0


class TestRecall:
    """Tests for recall metric."""

    def test_all_retrieved(self) -> None:
        """All relevant items are retrieved."""

        assert recall({"a.py"}, {"a.py"}) == 1.0

    def test_none_retrieved(self) -> None:
        """No relevant items are retrieved."""

        assert recall({"a.py"}, {"b.py"}) == 0.0

    def test_partial_retrieved(self) -> None:
        """Some relevant items are retrieved."""

        result = recall(
            {"a.py"},
            {"a.py", "b.py"},
        )

        assert result == 0.5

    def test_no_relevant(self) -> None:
        """No relevant items yields 0.0."""

        assert recall(set(), set()) == 0.0


class TestF1Score:
    """Tests for F1 score."""

    def test_perfect_scores(self) -> None:
        """Perfect precision and recall yields 1.0."""

        assert f1_score(1.0, 1.0) == 1.0

    def test_zero_precision(self) -> None:
        """Zero precision yields 0.0."""

        assert f1_score(0.0, 1.0) == 0.0

    def test_zero_recall(self) -> None:
        """Zero recall yields 0.0."""

        assert f1_score(1.0, 0.0) == 0.0

    def test_balanced(self) -> None:
        """Equal precision and recall produces same value."""

        result = f1_score(0.5, 0.5)

        assert result == 0.5

    def test_harmonic_mean(self) -> None:
        """F1 is the harmonic mean of precision and recall."""

        result = f1_score(0.8, 0.4)

        assert round(result, 4) == 0.5333


class TestReciprocalRank:
    """Tests for Mean Reciprocal Rank."""

    def test_first_result_relevant(self) -> None:
        """First result is relevant yields 1.0."""

        result = reciprocal_rank(
            ["a.py", "b.py"],
            {"a.py"},
        )

        assert result == 1.0

    def test_second_result_relevant(self) -> None:
        """Second result is relevant yields 0.5."""

        result = reciprocal_rank(
            ["a.py", "b.py"],
            {"b.py"},
        )

        assert result == 0.5

    def test_no_relevant_result(self) -> None:
        """No relevant result yields 0.0."""

        result = reciprocal_rank(
            ["a.py", "b.py"],
            {"c.py"},
        )

        assert result == 0.0

    def test_multiple_relevant(self) -> None:
        """Uses the rank of the first relevant result."""

        result = reciprocal_rank(
            ["a.py", "b.py", "c.py"],
            {"c.py", "a.py"},
        )

        assert result == 1.0
