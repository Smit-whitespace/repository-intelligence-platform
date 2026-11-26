"""Per-user secret files: created once, readable only by their owner."""

import os
from collections.abc import Callable
from pathlib import Path


def read_or_create_secret(
    path: Path,
    generate: Callable[[], str],
) -> str:
    """Return the secret stored at ``path``, creating it on first use.

    The file is created with mode 0600 (owner only, where the platform
    supports it). If another process creates it at the same moment,
    that process's secret is used, so all processes agree on one value.
    """

    try:
        return path.read_text(
            encoding="ascii",
        ).strip()

    except FileNotFoundError:
        pass

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    secret = generate()

    try:
        # O_EXCL: if another process created the file meanwhile, use theirs.
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )

    except FileExistsError:
        return path.read_text(
            encoding="ascii",
        ).strip()

    with os.fdopen(
        descriptor,
        "w",
        encoding="ascii",
    ) as file:
        file.write(
            secret,
        )

    return secret
