"""Retrieval evaluation runner."""

from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import (
    SearchQuery,
)
from app.indexing.retrieval_service import (
    RetrievalService,
)
from app.indexing.store_resolver import StaticVectorStoreResolver
from app.indexing.stores import VectorStore
from eval.metrics import (
    f1_score,
    precision,
    recall,
    reciprocal_rank,
)
from eval.models import (
    RetrievalEvalReport,
    RetrievalEvalResult,
    RetrievalTestCase,
)


class RetrievalEvaluator:
    """Evaluate retrieval quality against test cases.

    Parameters
    ----------
    retrieval_service:
        The retrieval service to evaluate.
    root_directory:
        Optional project root to scope every search to. When omitted,
        searches are unscoped, which returns no results; harnesses
        should always scope evaluation to a project.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        root_directory: str | None = None,
    ) -> None:
        """Initialize the evaluator."""

        self._retrieval_service = retrieval_service

        self._root_directory = root_directory

    def evaluate(
        self,
        test_cases: list[RetrievalTestCase],
        limit: int = 10,
    ) -> RetrievalEvalReport:
        """Run all test cases and produce an evaluation report."""

        results: list[RetrievalEvalResult] = []

        for case in test_cases:
            result = self._evaluate_single(
                case,
                limit=limit,
            )

            results.append(result)

        total = len(results)

        if total == 0:
            return RetrievalEvalReport(
                results=[],
                total_cases=0,
                avg_precision=0.0,
                avg_recall=0.0,
                avg_f1=0.0,
                avg_mrr=0.0,
            )

        avg_precision = sum(r.precision for r in results) / total

        avg_recall = sum(r.recall for r in results) / total

        avg_f1 = sum(r.f1 for r in results) / total

        avg_mrr = sum(r.mrr for r in results) / total

        return RetrievalEvalReport(
            results=results,
            total_cases=total,
            avg_precision=avg_precision,
            avg_recall=avg_recall,
            avg_f1=avg_f1,
            avg_mrr=avg_mrr,
        )

    def _evaluate_single(
        self,
        case: RetrievalTestCase,
        limit: int = 10,
    ) -> RetrievalEvalResult:
        """Evaluate a single test case."""

        response = self._retrieval_service.search(
            SearchQuery(
                query=case.query,
                root_directory=self._root_directory,
                limit=limit,
            ),
        )

        relevant = set(
            case.expected_file_paths,
        )

        retrieved_paths = [
            str(
                r.metadata.relative_path,
            )
            for r in response.results
        ]

        retrieved = set(
            retrieved_paths,
        )

        scores = [r.similarity_score for r in response.results]

        prec = precision(
            retrieved,
            relevant,
        )

        rec = recall(
            retrieved,
            relevant,
        )

        f1 = f1_score(
            prec,
            rec,
        )

        rr = reciprocal_rank(
            retrieved_paths,
            relevant,
        )

        return RetrievalEvalResult(
            test_case=case,
            retrieved_file_paths=retrieved_paths,
            retrieved_scores=scores,
            precision=prec,
            recall=rec,
            f1=f1,
            mrr=rr,
        )


def create_retrieval_evaluator(
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStore,
    root_directory: str | None = None,
) -> RetrievalEvaluator:
    """Convenience factory for creating a RetrievalEvaluator."""

    service = RetrievalService(
        embedding_provider=embedding_provider,
        vector_store_resolver=StaticVectorStoreResolver(
            vector_store,
        ),
    )

    return RetrievalEvaluator(
        retrieval_service=service,
        root_directory=root_directory,
    )
