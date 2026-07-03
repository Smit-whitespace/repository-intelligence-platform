"""Tests for Ollama embedding provider."""

from unittest.mock import MagicMock
from unittest.mock import patch

from app.core.config.models import OllamaSettings
from app.indexing.models import EmbeddingVector
from app.indexing.ollama_provider import (
    OllamaEmbeddingProvider,
)


def test_embed() -> None:
    """Generate embeddings."""

    settings = OllamaSettings()

    with patch(
        "app.indexing.ollama_provider.Client",
    ) as mock_client:
        client = MagicMock()

        client.embed.return_value.embeddings = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
        ]

        mock_client.return_value = client

        provider = OllamaEmbeddingProvider(
            settings,
        )

        embeddings = provider.embed(
            [
                "hello",
                "world",
            ]
        )

    assert embeddings == [
        EmbeddingVector(
            values=[1.0, 2.0, 3.0],
        ),
        EmbeddingVector(
            values=[4.0, 5.0, 6.0],
        ),
    ]

    client.embed.assert_called_once()