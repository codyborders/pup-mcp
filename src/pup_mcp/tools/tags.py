"""Datadog host tag management tools."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


class TagsGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str = Field(..., min_length=1, description="Hostname")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class TagsModifyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str = Field(..., min_length=1, description="Hostname")
    tags: List[str] = Field(..., min_length=1, description="Tags list")


class TagsDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str = Field(..., min_length=1, description="Hostname")


async def list_tags(params: PaginatedInput) -> str:
    """List all host tags across the infrastructure."""
    try:
        data = await api_request("tags/hosts", "v1")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def get_tags(params: TagsGetInput) -> str:
    """Get all tags for a specific host."""
    try:
        data = await api_request(f"tags/hosts/{params.host}", "v1")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def add_tags(params: TagsModifyInput) -> str:
    """Add tags to a host."""
    try:
        data = await api_request(
            f"tags/hosts/{params.host}", "v1", method="POST", json_body={"tags": params.tags}
        )
        return format_output(data, ResponseFormat.JSON)
    except Exception as exc:
        return handle_error(exc)


async def update_tags(params: TagsModifyInput) -> str:
    """Replace all tags on a host."""
    try:
        data = await api_request(
            f"tags/hosts/{params.host}", "v1", method="PUT", json_body={"tags": params.tags}
        )
        return format_output(data, ResponseFormat.JSON)
    except Exception as exc:
        return handle_error(exc)


async def delete_tags(params: TagsDeleteInput) -> str:
    """Delete all tags from a host."""
    try:
        await api_request(f"tags/hosts/{params.host}", "v1", method="DELETE")
        return f"All tags deleted from host '{params.host}'."
    except Exception as exc:
        return handle_error(exc)
