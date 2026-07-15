"""Shared API schemas."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ErrorResponse(BaseModel):
    """Standard API error response."""

    detail: str = Field(
        description="Human-readable error detail.",
        examples=[
            "Repository does not exist.",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Repository does not exist.",
            },
        },
    )
