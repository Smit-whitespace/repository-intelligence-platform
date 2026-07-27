"""Evaluation domain models."""

from pydantic import BaseModel


class RetrievalTestCase(BaseModel):
    """A single retrieval evaluation case.

    Attributes
    ----------
    query:
        The search query to run.
    expected_file_paths:
        File paths that should appear in the results.
    expected_content:
        Optional content snippets expected in results.
    expected_concepts:
        Optional architectural concepts or keywords relevant to the query.
    expected_symbols:
        Optional code symbols (function names, class names) expected.
    """

    query: str

    expected_file_paths: list[str]

    expected_content: list[str] | None = None

    expected_concepts: list[str] | None = None

    expected_symbols: list[str] | None = None


class RetrievalEvalResult(BaseModel):
    """Result of evaluating one test case.

    Attributes
    ----------
    test_case:
        The test case that was evaluated.
    retrieved_file_paths:
        File paths actually returned by retrieval.
    retrieved_scores:
        Similarity scores for each retrieved file.
    precision:
        Precision@k for this case.
    recall:
        Recall@k for this case.
    f1:
        F1 score for this case.
    mrr:
        Mean Reciprocal Rank — inverse of the first relevant position.
    """

    test_case: RetrievalTestCase

    retrieved_file_paths: list[str]

    retrieved_scores: list[float]

    precision: float

    recall: float

    f1: float

    mrr: float


class RetrievalEvalReport(BaseModel):
    """Aggregated evaluation report.

    Attributes
    ----------
    results:
        Per-test-case results.
    total_cases:
        Number of test cases run.
    avg_precision:
        Average precision across all cases.
    avg_recall:
        Average recall across all cases.
    avg_f1:
        Average F1 across all cases.
    avg_mrr:
        Average MRR across all cases.
    """

    results: list[RetrievalEvalResult]

    total_cases: int

    avg_precision: float

    avg_recall: float

    avg_f1: float

    avg_mrr: float
