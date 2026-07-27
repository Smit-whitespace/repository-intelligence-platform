"""Retrieval evaluation metrics."""


def precision(
    retrieved: set[str],
    relevant: set[str],
) -> float:
    """Fraction of retrieved items that are relevant.

    Returns 0.0 when no items are retrieved.
    """

    if not retrieved:
        return 0.0

    relevant_retrieved = retrieved & relevant

    return len(relevant_retrieved) / len(retrieved)


def recall(
    retrieved: set[str],
    relevant: set[str],
) -> float:
    """Fraction of relevant items that are retrieved.

    Returns 0.0 when no relevant items exist.
    """

    if not relevant:
        return 0.0

    relevant_retrieved = retrieved & relevant

    return len(relevant_retrieved) / len(relevant)


def f1_score(
    prec: float,
    rec: float,
) -> float:
    """Harmonic mean of precision and recall.

    Returns 0.0 when both precision and recall are 0.
    """

    if prec + rec == 0.0:
        return 0.0

    return 2.0 * prec * rec / (prec + rec)


def reciprocal_rank(
    retrieved: list[str],
    relevant: set[str],
) -> float:
    """Inverse of the rank of the first relevant result.

    Returns 0.0 when no relevant result is found.
    """

    for rank, path in enumerate(
        retrieved,
        start=1,
    ):
        if path in relevant:
            return 1.0 / rank

    return 0.0
