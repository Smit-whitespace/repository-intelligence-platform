"""The API token every REST request must carry (ADR-0020).

The API listens on 127.0.0.1 and accepts only local Host headers, but
any process on the machine could still call it, including processes of
other user accounts. Every request except ``/health`` must therefore
send ``Authorization: Bearer <token>``. The token is created on first
use in a per-user file (``~/.local_openclaw/api.token``, readable only
by its owner). At startup the backend prints a sign-in link carrying a
single-use code, never the token itself, which the app exchanges for the
token once.

A process running as the same user can read the token file. The token
does not stop that; it makes such use deliberate (reading a secret file),
which agent permission rules can forbid. See ADR-0020.
"""

import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config.settings import settings
from app.core.storage.locations import PROJECT_STORAGE_DIRECTORY_NAME
from app.core.storage.secret_file import read_or_create_secret

API_TOKEN_FILE_NAME = "api.token"

_bearer = HTTPBearer(
    auto_error=False,
    description="The token in ~/.local_openclaw/api.token.",
)


def api_token_path() -> Path:
    """Return the token file path (``LOC_API_TOKEN_PATH`` overrides it)."""

    if settings.security.api_token_path:
        return Path(
            settings.security.api_token_path,
        ).expanduser()

    return Path.home() / PROJECT_STORAGE_DIRECTORY_NAME / API_TOKEN_FILE_NAME


@lru_cache(maxsize=1)
def api_token() -> str:
    """Load the per-user API token, creating it on first use."""

    return read_or_create_secret(
        api_token_path(),
        lambda: secrets.token_urlsafe(32),
    )


SIGN_IN_CODE_TTL_SECONDS = 600
"""How long a printed sign-in link works (it also stops after one use)."""


@dataclass
class _SignInCode:
    digest: bytes

    expires_at: float

    used: bool = False


_sign_in_lock = threading.Lock()

_sign_in_code: _SignInCode | None = None


def _digest(
    code: str,
) -> bytes:
    return hashlib.sha256(
        code.encode(
            "utf-8",
        ),
    ).digest()


def issue_sign_in_code() -> str:
    """Create a single-use sign-in code, replacing any earlier one.

    The printed sign-in link carries this code, never the API token, so
    startup output and log files kept afterwards do not reveal the token:
    the code stops working after one use or ``SIGN_IN_CODE_TTL_SECONDS``.
    Only its hash is kept in memory.
    """

    global _sign_in_code

    code = secrets.token_urlsafe(
        24,
    )

    with _sign_in_lock:
        _sign_in_code = _SignInCode(
            digest=_digest(
                code,
            ),
            expires_at=time.monotonic() + SIGN_IN_CODE_TTL_SECONDS,
        )

    return code


def redeem_sign_in_code(
    code: str,
) -> str | None:
    """Return the API token for a valid, unused, unexpired code."""

    with _sign_in_lock:
        current = _sign_in_code

        if (
            current is None
            or current.used
            or time.monotonic() > current.expires_at
            or not hmac.compare_digest(
                _digest(
                    code,
                ),
                current.digest,
            )
        ):
            return None

        current.used = True

    return api_token()


def sign_in_url() -> str:
    """A new single-use link that signs the RIP app in."""

    return f"{settings.server.frontend_url.rstrip('/')}/?" + urlencode(
        {
            "code": issue_sign_in_code(),
        },
    )


def require_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """Reject a request without the right ``Authorization: Bearer`` token."""

    # compare_digest: the comparison time must not reveal how much of a
    # guessed token was right.
    if credentials is None or not hmac.compare_digest(
        credentials.credentials.encode(
            "utf-8",
        ),
        api_token().encode(
            "utf-8",
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Missing or wrong API token. Open the sign-in link the RIP "
                "backend printed when it started."
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )
