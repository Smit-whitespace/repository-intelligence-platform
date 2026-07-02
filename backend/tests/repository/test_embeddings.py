"""Tests for embedding abstractions."""

from app.repository.embeddings import (
    EmbeddingProvider,
)


class FakeEmbeddingProvider(
    EmbeddingProvider,
):
    """Fake embedding provider."""

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Return deterministic embeddings."""

        return [
            [float(index)]
            for index, _ in enumerate(
                texts,
            )
        ]


def test_fake_embedding_provider() -> None:
    """Embedding provider should return one embedding per text."""

    provider = FakeEmbeddingProvider()

    embeddings = provider.embed(
        [
            "hello",
            "world",
        ],
    )

    assert len(embeddings) == 2

    assert embeddings[0] == [0.0]

    assert embeddings[1] == [1.0]