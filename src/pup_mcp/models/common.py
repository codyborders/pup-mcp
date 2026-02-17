"""Shared Pydantic models and enums used across tools."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    JSON = "json"
    MARKDOWN = "markdown"


class PaginatedInput(BaseModel):
    """Base input model for paginated list endpoints."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: int = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description="Maximum results to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip for pagination",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' or 'markdown'",
    )
