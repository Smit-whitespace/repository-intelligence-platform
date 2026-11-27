"""Detect files that changed since the last semantic index."""

from dataclasses import dataclass, field
from pathlib import Path

from app.indexing.indexer import RepositoryIndexer
from app.repository.hashing import calculate_sha256
from app.repository.ignore import is_indexable_file_name
from app.repository.metadata import RepositoryMetadataExtractor
from app.repository.scanner import RepositoryScanner


@dataclass(frozen=True)
class ChangeSet:
    """Files that differ from the index, in the stored path form."""

    changed: list[str] = field(default_factory=list)

    added: list[str] = field(default_factory=list)

    removed: list[str] = field(default_factory=list)

    modified_ns: dict[str, int] = field(
        default_factory=dict,
        compare=False,
        repr=False,
    )

    @property
    def to_index(self) -> list[str]:
        """Files to (re-)index, most recently modified first."""

        return sorted(
            [*self.changed, *self.added],
            key=lambda path: self.modified_ns.get(path, 0),
            reverse=True,
        )

    @property
    def total(self) -> int:
        return len(self.changed) + len(self.added) + len(self.removed)


class FileHashCache:
    """SHA-256 per file, reused while its mtime and size are unchanged."""

    def __init__(self) -> None:
        self._entries: dict[Path, tuple[int, int, str]] = {}

    def sha256(self, path: Path) -> str:
        """Hash a file; raises ``OSError`` if it is gone or unreadable."""

        stat = path.stat()

        cached = self._entries.get(path)

        if cached is not None and cached[:2] == (stat.st_mtime_ns, stat.st_size):
            return cached[2]

        digest = calculate_sha256(path)

        self._entries[path] = (stat.st_mtime_ns, stat.st_size, digest)

        return digest


def detect_changes(
    root_directory: Path,
    scanner: RepositoryScanner,
    metadata_extractor: RepositoryMetadataExtractor,
    indexer: RepositoryIndexer,
    cache: FileHashCache,
) -> ChangeSet:
    """Compare the files on disk with what the index holds.

    "Current" files are the ones indexing would index: not directories,
    indexable by name, and text. A file that vanishes mid-scan counts as
    removed if it was indexed, and is ignored otherwise.
    """

    root_directory = root_directory.resolve()

    indexed = indexer.indexed_file_hashes(
        str(root_directory),
    )

    changed: list[str] = []

    added: list[str] = []

    modified_ns: dict[str, int] = {}

    seen: set[str] = set()

    for entry in scanner.scan(root_directory):
        if entry.is_directory or not is_indexable_file_name(entry.name):
            continue

        relative_path = str(entry.relative_path)

        try:
            metadata_extractor.enrich_fast(entry)

            if not entry.is_text_file:
                continue

            digest = cache.sha256(entry.absolute_path)

            modified_ns[relative_path] = entry.absolute_path.stat().st_mtime_ns

        except OSError:
            continue

        seen.add(relative_path)

        stored = indexed.get(relative_path)

        if stored is None:
            added.append(relative_path)

        elif stored != digest:
            changed.append(relative_path)

    return ChangeSet(
        changed=changed,
        added=added,
        removed=sorted(set(indexed) - seen),
        modified_ns=modified_ns,
    )
