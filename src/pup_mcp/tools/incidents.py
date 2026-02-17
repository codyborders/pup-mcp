"""Datadog incident management tools."""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


class IncidentGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str = Field(..., min_length=1, description="Incident ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


def _incidents_md(data: Any) -> str:
    incidents: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    if not incidents:
        return "No incidents found."
    lines = [f"# Incidents ({len(incidents)})", ""]
    for inc in incidents:
        attrs = inc.get("attributes", {})
        lines.append(f"## {attrs.get('title', '?')} ({inc.get('id')})")
        lines.append(f"- **Status**: {attrs.get('state', '?')}")
        lines.append(f"- **Severity**: {attrs.get('severity', 'N/A')}")
        lines.append(f"- **Created**: {attrs.get('created', '?')}")
        lines.append("")
    return "\n".join(lines)


async def list_incidents(params: PaginatedInput) -> str:
    """List Datadog incidents with pagination."""
    try:
        qp: Dict[str, Any] = {"page[size]": params.limit, "page[offset]": params.offset}
        data = await api_request("incidents", "v2", params=qp)
        return format_output(data, params.response_format, _incidents_md)
    except Exception as exc:
        return handle_error(exc)


async def get_incident(params: IncidentGetInput) -> str:
    """Get detailed information for a specific Datadog incident."""
    try:
        data = await api_request(f"incidents/{params.incident_id}", "v2")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)
