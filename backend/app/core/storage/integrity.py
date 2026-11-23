"""Integrity of RIP's own state files stored inside repositories.

Proposals, snapshots and validation commands live in the project's
``.local_openclaw`` directory. That directory is ordinary repository
content: cloning a repository can bring a ``.local_openclaw`` with it.
Without a check, a malicious repository could ship validation commands
that run the first time someone applies an edit, or a proposal whose
stored contents differ from the diff it displays.

So RIP signs every such file it writes with an HMAC-SHA256 key that
lives outside any repository (``~/.local_openclaw/integrity.key``), and
refuses files whose signature is missing or wrong. A signature is bound
to the purpose of the file and to the resolved project root, so a signed
file can be neither repurposed nor copied into another project.

Anyone who can read the key file can forge signatures, but such a party
already runs as the user; the threat this addresses is content that
arrives with a repository.
"""

import hashlib
import hmac
import json
import os
import secrets
from functools import lru_cache
from pathlib import Path

from app.core.config.settings import settings
from app.core.storage.locations import PROJECT_STORAGE_DIRECTORY_NAME

INTEGRITY_KEY_FILE_NAME = "integrity.key"


def integrity_key_path() -> Path:
    """Return the key file path (``LOC_INTEGRITY_KEY_PATH`` overrides it)."""

    if settings.security.integrity_key_path:
        return Path(
            settings.security.integrity_key_path,
        ).expanduser()

    return Path.home() / PROJECT_STORAGE_DIRECTORY_NAME / INTEGRITY_KEY_FILE_NAME


@lru_cache(maxsize=1)
def _key() -> bytes:
    """Load the per-user key, creating it on first use."""

    path = integrity_key_path()

    try:
        return bytes.fromhex(
            path.read_text(
                encoding="ascii",
            ).strip(),
        )

    except FileNotFoundError:
        pass

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    key = secrets.token_bytes(
        32,
    )

    try:
        # O_EXCL: if another process created the key meanwhile, use theirs.
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )

    except FileExistsError:
        return bytes.fromhex(
            path.read_text(
                encoding="ascii",
            ).strip(),
        )

    with os.fdopen(
        descriptor,
        "w",
        encoding="ascii",
    ) as file:
        file.write(
            key.hex(),
        )

    return key


def _canonical(
    document: object,
    purpose: str,
    root: Path | None,
) -> bytes:
    return json.dumps(
        {
            "purpose": purpose,
            "root": str(root.resolve()) if root is not None else "",
            "document": document,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode(
        "utf-8",
    )


def sign(
    document: object,
    purpose: str,
    root: Path | None,
) -> str:
    """Return the signature of a JSON-compatible document."""

    return hmac.new(
        _key(),
        _canonical(
            document,
            purpose,
            root,
        ),
        hashlib.sha256,
    ).hexdigest()


def verify(
    document: object,
    signature: object,
    purpose: str,
    root: Path | None,
) -> bool:
    """Return whether ``signature`` was made by this installation."""

    if not isinstance(signature, str):
        return False

    return hmac.compare_digest(
        signature,
        sign(
            document,
            purpose,
            root,
        ),
    )
