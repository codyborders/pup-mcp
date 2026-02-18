"""Datadog user and role management tools."""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


class UserGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(..., min_length=1, description="User ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


def _users_md(data: Any) -> str:
    users: List[Dict[str, Any]] = data.get("users", []) if isinstance(data, dict) else []
    if not users:
        return "No users found."
    lines = [f"# Users ({len(users)})", ""]
    for u in users:
        lines.append(f"## {u.get('name', '?')} ({u.get('handle', '?')})")
        lines.append(f"- **Email**: {u.get('email', '?')}")
        lines.append(f"- **Role**: {u.get('role', '?')}")
        lines.append(f"- **Disabled**: {u.get('disabled', False)}")
        lines.append("")
    return "\n".join(lines)


async def list_users(params: PaginatedInput) -> str:
    """List users in the Datadog organization."""
    try:
        data = await api_request("user", "v1")
        return format_output(data, params.response_format, _users_md)
    except Exception as exc:
        return handle_error(exc)


async def get_user(params: UserGetInput) -> str:
    """Get details for a specific Datadog user."""
    try:
        data = await api_request(f"user/{params.user_id}", "v1")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def list_roles() -> str:
    """List available roles in the Datadog organization."""
    try:
        data = await api_request("roles", "v2")
        return format_output(data, ResponseFormat.JSON)
    except Exception as exc:
        return handle_error(exc)
