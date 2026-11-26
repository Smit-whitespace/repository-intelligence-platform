"""The API token every REST request must carry (ADR-0020).

The API listens on 127.0.0.1 and accepts only local Host headers, but
any process on the machine could still call it, including processes of
other user accounts. Every request except ``/health`` must therefore
send ``Authorization: Bearer <token>``. The token is created on first
use in a per-user file (``~/.local_openclaw/api.token``, readable only
by its owner); the backend prints a sign-in link for the app at startup.

A process running as the same user can read the token file. The token
does not stop that; it makes such use deliberate (reading a secret file),
which agent permission rules can forbid. See ADR-0020.
"""

import hmac
import secrets
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


def sign_in_url() -> str:
    """The link that signs the RIP app in (it stores the token)."""

    return f"{settings.server.frontend_url.rstrip('/')}/?" + urlencode(
        {
            "token": api_token(),
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
