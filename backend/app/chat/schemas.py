"""Chat API schemas."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ChatRequest(BaseModel):
    """Chat request."""

    query: str = Field(
        description="User question to answer using repository context.",
        examples=[
            "Explain the editing workflow.",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Explain the editing workflow.",
            },
        },
    )


class ChatResponse(BaseModel):
    """Chat response."""

    content: str = Field(
        description="Generated repository-aware answer.",
        examples=[
            "The editing workflow creates a ChangeSet before applying it.",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": (
                    "The editing workflow creates a ChangeSet before applying it."
                ),
            },
        },
    )
