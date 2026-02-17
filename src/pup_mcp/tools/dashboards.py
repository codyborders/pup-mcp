"""Datadog dashboard management tools."""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


# -- Input models -----------------------------------------------------------

class DashboardGetInput(BaseModel):
    """Input for getting a single dashboard."""

    model_config = ConfigDict(extra="forbid")

    dashboard_id: str = Field(
        ..., min_length=1, description="Dashboard ID (e.g. 'abc-def-ghi')"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON, description="Output format"
    )


class DashboardDeleteInput(BaseModel):
    """Input for deleting a dashboard."""

    model_config = ConfigDict(extra="forbid")

    dashboard_id: str = Field(..., min_length=1, description="Dashboard ID to delete")


# -- Markdown helpers -------------------------------------------------------

def _dashboards_list_md(data: Any) -> str:
    dashboards: List[Dict[str, Any]] = (
        data.get("dashboards", []) if isinstance(data, dict) else []
    )
    if not dashboards:
        return "No dashboards found."
    lines = [f"# Dashboards ({len(dashboards)})", ""]
    for db in dashboards:
        lines.append(f"## {db.get('title', '?')} ({db.get('id')})")
        if db.get("description"):
            lines.append(f"  {db['description']}")
        if db.get("author_handle"):
            lines.append(f"  - **Author**: {db['author_handle']}")
        lines.append("")
    return "\n".join(lines)


def _dashboard_detail_md(data: Any) -> str:
    db: Dict[str, Any] = data
    widgets = db.get("widgets", [])
    return "\n".join([
        f"# Dashboard: {db.get('title')}",
        "",
        f"- **ID**: {db.get('id')}",
        f"- **Layout**: {db.get('layout_type')}",
        f"- **Widgets**: {len(widgets)}",
        f"- **Description**: {db.get('description') or '(none)'}",
        f"- **Author**: {db.get('author_handle', 'unknown')}",
        f"- **Created**: {db.get('created_at')}",
        f"- **Modified**: {db.get('modified_at')}",
    ])


# -- Tool implementations --------------------------------------------------

async def list_dashboards(params: PaginatedInput) -> str:
    """List all dashboards in the Datadog account.

    Args:
        params: Pagination and response format options.

    Returns:
        Dashboard summaries as JSON or Markdown.
    """
    try:
        data = await api_request("dashboard", "v1")
        return format_output(data, params.response_format, _dashboards_list_md)
    except Exception as exc:
        return handle_error(exc)


async def get_dashboard(params: DashboardGetInput) -> str:
    """Get full configuration for a Datadog dashboard.

    Args:
        params: Contains dashboard_id and response_format.

    Returns:
        Complete dashboard definition.
    """
    try:
        data = await api_request(f"dashboard/{params.dashboard_id}", "v1")
        return format_output(data, params.response_format, _dashboard_detail_md)
    except Exception as exc:
        return handle_error(exc)


async def delete_dashboard(params: DashboardDeleteInput) -> str:
    """Permanently delete a Datadog dashboard.

    Args:
        params: Contains dashboard_id to delete.

    Returns:
        Confirmation message or error string.
    """
    try:
        await api_request(
            f"dashboard/{params.dashboard_id}", "v1", method="DELETE"
        )
        return f"Dashboard {params.dashboard_id} deleted successfully."
    except Exception as exc:
        return handle_error(exc)
