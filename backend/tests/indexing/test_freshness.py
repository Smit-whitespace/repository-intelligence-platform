"""Index freshness: reading the per-file hashes stored in the index."""

from app.indexing.indexer import RepositoryIndexer
from app.repository.hashing import calculate_sha256
from tests.indexing.test_incremental_indexing import (  # noqa: F401
    CountingEmbedder,
    _index,
    project,
    resolver,
)


def test_indexed_file_hashes_match_the_files(project, resolver):  # noqa: F811
    _index(project, CountingEmbedder(), resolver)
    indexer = RepositoryIndexer(
        embedding_provider=CountingEmbedder(),
        vector_store_resolver=resolver,
    )

    hashes = indexer.indexed_file_hashes(str(project.resolve()))

    assert set(hashes) == {"main.py", "utils.py"}
    assert hashes["main.py"] == calculate_sha256(project / "main.py")
