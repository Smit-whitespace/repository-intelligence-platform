"""Python chunk boundaries: what one search hit contains."""

from pathlib import Path

from app.repository.chunking import RepositoryChunker
from app.repository.documents import RepositoryDocumentLoader
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.models import ChunkType, RepositoryChunk, RepositoryEntry


def _chunks(
    tmp_path: Path,
    source: str,
) -> list[RepositoryChunk]:
    file_path = tmp_path / "module.py"

    file_path.write_text(
        source,
        encoding="utf-8",
    )

    entry = RepositoryEntry(
        name="module.py",
        absolute_path=file_path,
        relative_path=Path("module.py"),
        is_directory=False,
    )

    RepositoryMetadataExtractor().enrich(
        entry,
    )

    return RepositoryChunker().chunk(
        RepositoryDocumentLoader().load(
            entry,
        ),
    )


def test_imports_and_constants_form_one_module_chunk(
    tmp_path: Path,
) -> None:
    """One-line chunks (a lone import) used to crowd out real code."""

    chunks = _chunks(
        tmp_path,
        '"""Signing helpers."""\n'
        "\n"
        "import hmac\n"
        "import hashlib\n"
        "\n"
        "# Purposes a signature can be bound to.\n"
        'PURPOSES = ("proposal", "snapshot")\n'
        "\n"
        "\n"
        "def sign(data):\n"
        "    return hmac.new(b'k', data, hashlib.sha256).hexdigest()\n",
    )

    assert [chunk.boundary.chunk_type for chunk in chunks] == [
        ChunkType.MODULE,
        ChunkType.FUNCTION,
    ]

    header = chunks[0]

    assert (header.boundary.start_line, header.boundary.end_line) == (1, 7)

    # The comment between statements is kept with them.
    assert "# Purposes a signature can be bound to." in header.content


def test_module_statements_after_a_function_start_a_new_chunk(
    tmp_path: Path,
) -> None:
    chunks = _chunks(
        tmp_path,
        "import os\n\n\ndef first():\n    return 1\n\n\nLIMIT = 3\nNAME = 'x'\n",
    )

    assert [
        (chunk.boundary.chunk_type, chunk.boundary.start_line, chunk.boundary.end_line)
        for chunk in chunks
    ] == [
        (ChunkType.MODULE, 1, 1),
        (ChunkType.FUNCTION, 4, 5),
        (ChunkType.MODULE, 8, 9),
    ]


def test_merged_module_chunks_stay_within_the_line_limit(
    tmp_path: Path,
) -> None:
    chunks = _chunks(
        tmp_path,
        "".join(f"VALUE_{number} = {number}\n" for number in range(250)),
    )

    assert [
        (chunk.boundary.start_line, chunk.boundary.end_line)
        for chunk in chunks
    ] == [
        (1, 100),
        (101, 200),
        (201, 250),
    ]


def test_decorators_belong_to_their_function(
    tmp_path: Path,
) -> None:
    """A route's path lives in its decorator; search must see it."""

    chunks = _chunks(
        tmp_path,
        "import router\n"
        "\n"
        "\n"
        '@router.post(\n    "/proposals/{proposal_id}/apply",\n)\n'
        "def apply_proposal(proposal_id):\n"
        "    return proposal_id\n",
    )

    function = chunks[-1]

    assert function.boundary.chunk_type is ChunkType.FUNCTION

    assert function.boundary.start_line == 4

    assert '"/proposals/{proposal_id}/apply"' in function.content
