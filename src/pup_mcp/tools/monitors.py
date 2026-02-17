"""Datadog monitor management tools."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


# -- Input models -----------------------------------------------------------

class MonitorsListInput(PaginatedInput):
    """Input for listing monitors."""

    name: Optional[str] = Field(
        default=None, description="Filter by monitor name substring"
    )
    tags: Optional[str] = Field(
        default=None,
        description="Comma-separated tags (e.g. 'env:prod,team:backend')",
    )


class MonitorGetInput(BaseModel):
    """Input for getting a single monitor."""

    model_config = ConfigDict(extra="forbid")

    monitor_id: int = Field(..., gt=0, description="Numeric monitor ID")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON, description="Output format"
    )


class MonitorsSearchInput(BaseModel):
    """Input for searching monitors."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ..., min_length=1, description="Search query (e.g. 'type:metric status:alert')"
    )
    page: int = Field(default=0, ge=0, description="Page number")
    per_page: int = Field(default=30, ge=1, le=100, description="Results per page")
    sort: Optional[str] = Field(
        default=None, description="Sort specification (e.g. 'name,asc')"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON, description="Output format"
    )


class MonitorDeleteInput(BaseModel):
    """Input for deleting a monitor."""

    model_config = ConfigDict(extra="forbid")

    monitor_id: int = Field(..., gt=0, description="Numeric monitor ID to delete")


# -- Markdown helpers -------------------------------------------------------

def _monitors_list_md(data: Any) -> str:
    monitors: List[Dict[str, Any]] = data if isinstance(data, list) else []
    if not monitors:
        return "No monitors found."
    lines = [f"# Monitors ({len(monitors)} results)", ""]
    for m in monitors:
        lines.append(f"## {m.get('name', '?')} (ID: {m.get('id')})")
        lines.append(f"- **Type**: {m.get('type')}")
        lines.append(f"- **Status**: {m.get('overall_state')}")
        tags = m.get("tags", [])
        if tags:
            lines.append(f"- **Tags**: {', '.join(tags)}")
        lines.append("")
    return "\n".join(lines)


def _monitor_detail_md(data: Any) -> str:
    m: Dict[str, Any] = data
    lines = [
        f"# Monitor: {m.get('name')}",
        "",
        f"- **ID**: {m.get('id')}",
        f"- **Type**: {m.get('type')}",
        f"- **Status**: {m.get('overall_state')}",
        f"- **Query**: `{m.get('query')}`",
        f"- **Message**: {m.get('message') or '(none)'}",
        f"- **Created**: {m.get('created')}",
        f"- **Modified**: {m.get('modified')}",
    ]
    tags = m.get("tags", [])
    if tags:
        lines.append(f"- **Tags**: {', '.join(tags)}")
    return "\n".join(lines)


# -- Tool implementations --------------------------------------------------

async def list_monitors(params: MonitorsListInput) -> str:
    """List Datadog monitors with optional name/tag filtering.

    Args:
        params: Filtering and pagination options.

    Returns:
        Formatted monitor list as JSON or Markdown.
    """
    try:
        qp: Dict[str, Any] = {
            "page_size": params.limit,
            "page": params.offset // params.limit,
        }
        if params.name:
            qp["name"] = params.name
        if params.tags:
            qp["monitor_tags"] = params.tags
        data = await api_request("monitor", "v1", params=qp)
        return format_output(data, params.response_format, _monitors_list_md)
    except Exception as exc:
        return handle_error(exc)


async def get_monitor(params: MonitorGetInput) -> str:
    """Get detailed configuration for a Datadog monitor.

    Args:
        params: Contains the monitor_id and response_format.

    Returns:
        Full monitor definition as JSON or Markdown.
    """
    try:
        data = await api_request(f"monitor/{params.monitor_id}", "v1")
        return format_output(data, params.response_format, _monitor_detail_md)
    except Exception as exc:
        return handle_error(exc)


async def search_monitors(params: MonitorsSearchInput) -> str:
    """Search monitors using Datadog query syntax.

    Args:
        params: Search query, pagination, and sort options.

    Returns:
        Matching monitors with metadata.
    """
    try:
        qp: Dict[str, Any] = {
            "query": params.query,
            "page": params.page,
            "per_page": params.per_page,
        }
        if params.sort:
            qp["sort"] = params.sort
        data = await api_request("monitor/search", "v1", params=qp)
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def delete_monitor(params: MonitorDeleteInput) -> str:
    """Permanently delete a Datadog monitor.

    Args:
        params: Contains the monitor_id to delete.

    Returns:
        Confirmation message or error string.
    """
    try:
        await api_request(f"monitor/{params.monitor_id}", "v1", method="DELETE")
        return f"Monitor {params.monitor_id} deleted successfully."
    except Exception as exc:
        return handle_error(exc)
