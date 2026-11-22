"""Tests for the inter-process index lock."""

from pathlib import Path

import pytest

from app.indexing.exceptions import IndexingBusyError
from app.indexing.lock import project_index_lock


def test_second_holder_is_refused_until_release(
    tmp_path: Path,
) -> None:
    """OS file locks conflict across separate opens, as across processes."""

    with project_index_lock(
        tmp_path,
    ):
        with pytest.raises(
            IndexingBusyError,
        ):
            with project_index_lock(
                tmp_path,
            ):
                pass

    with project_index_lock(
        tmp_path,
    ):
        pass


def test_lock_is_released_when_the_body_raises(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        with project_index_lock(
            tmp_path,
        ):
            raise ValueError("indexing failed")

    with project_index_lock(
        tmp_path,
    ):
        pass


def test_lock_held_by_another_process_blocks_indexing(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys
    import textwrap

    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                f"""
                import sys, time
                sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r})
                from app.indexing.lock import project_index_lock
                with project_index_lock({str(tmp_path)!r}):
                    print("locked", flush=True)
                    time.sleep(30)
                """,
            ),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )

    try:
        assert holder.stdout is not None

        assert holder.stdout.readline().strip() == "locked"

        with pytest.raises(
            IndexingBusyError,
        ):
            with project_index_lock(
                tmp_path,
            ):
                pass

    finally:
        holder.kill()

        holder.wait()

    # The OS releases the lock when the holder dies. On Windows the
    # release can lag the process exit slightly, so allow a few seconds.
    import time

    deadline = time.monotonic() + 5

    while True:
        try:
            with project_index_lock(
                tmp_path,
            ):
                break

        except IndexingBusyError:
            if time.monotonic() > deadline:
                raise

            time.sleep(0.05)
