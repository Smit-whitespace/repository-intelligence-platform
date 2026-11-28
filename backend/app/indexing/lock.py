"""Inter-process lock around writes to a project's index.

The RIP app and an MCP server started by an agent can both index the
same project. ChromaDB's persistent client is not safe for concurrent
writers in separate processes, so indexing takes an exclusive,
non-blocking OS file lock first. The operating system releases the lock
when the holding process exits, even after a crash, so a stale lock can
never block indexing forever.
"""

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.core.storage.locations import project_storage_directory
from app.indexing.exceptions import IndexingBusyError

INDEX_LOCK_RELATIVE_PATH = Path("index/index.lock")


@contextmanager
def project_index_lock(
    root_directory: str | Path,
) -> Iterator[None]:
    """Hold the project's index lock, or raise ``IndexingBusyError``."""

    lock_path = (
        project_storage_directory(
            root_directory,
        )
        / INDEX_LOCK_RELATIVE_PATH
    )

    lock_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor = os.open(
        lock_path,
        os.O_RDWR | os.O_CREAT,
    )

    try:
        if not _try_lock(
            descriptor,
        ):
            # The holder may be this process (a background update) or
            # another one (the app and an MCP server), so name neither.
            raise IndexingBusyError(
                "Another index update is running for this project; try "
                "again shortly.",
            )

        try:
            yield

        finally:
            _unlock(
                descriptor,
            )

    finally:
        os.close(
            descriptor,
        )


if sys.platform == "win32":
    import msvcrt

    def _try_lock(
        descriptor: int,
    ) -> bool:
        os.lseek(
            descriptor,
            0,
            os.SEEK_SET,
        )

        try:
            msvcrt.locking(
                descriptor,
                msvcrt.LK_NBLCK,
                1,
            )

        except OSError:
            return False

        return True

    def _unlock(
        descriptor: int,
    ) -> None:
        os.lseek(
            descriptor,
            0,
            os.SEEK_SET,
        )

        msvcrt.locking(
            descriptor,
            msvcrt.LK_UNLCK,
            1,
        )

else:
    import fcntl

    def _try_lock(
        descriptor: int,
    ) -> bool:
        try:
            fcntl.flock(
                descriptor,
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )

        except OSError:
            return False

        return True

    def _unlock(
        descriptor: int,
    ) -> None:
        fcntl.flock(
            descriptor,
            fcntl.LOCK_UN,
        )
