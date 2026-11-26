"""Sign-in: exchange the single-use code from the startup link for the token."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security.api_token import redeem_sign_in_code

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


class SignInRequest(BaseModel):
    """The code from the sign-in link the backend printed at startup."""

    code: str = Field(
        min_length=1,
        max_length=200,
    )


class SignInResponse(BaseModel):
    """The API token to send as ``Authorization: Bearer <token>``."""

    token: str


@router.post(
    "/sign-in",
    response_model=SignInResponse,
    operation_id="signIn",
    summary="Exchange a sign-in code for the API token",
    description=(
        "Open endpoint: the code is the credential. Each code works once and "
        "for ten minutes; restart the backend for a new link, or paste the "
        "token from ~/.local_openclaw/api.token."
    ),
    responses={
        401: {
            "description": "The code is wrong, already used, or expired.",
        },
    },
)
def sign_in(
    request: SignInRequest,
) -> SignInResponse:
    """Return the API token for a valid sign-in code."""

    token = redeem_sign_in_code(
        request.code,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "This sign-in link has expired or was already used. Restart "
                "the backend for a new link, or paste the token from "
                "~/.local_openclaw/api.token."
            ),
        )

    return SignInResponse(
        token=token,
    )
