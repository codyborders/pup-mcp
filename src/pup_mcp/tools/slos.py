"""Datadog SLO management tools."""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


class SloGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class SloDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID to delete")


def _slos_md(data: Any) -> str:
    slos: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    if not slos:
        return "No SLOs found."
    lines = [f"# SLOs ({len(slos)})", ""]
    for s in slos:
        lines.append(f"## {s.get('name', '?')} ({s.get('id')})")
        lines.append(f"- **Type**: {s.get('type')}")
        lines.append(f"- **Description**: {s.get('description') or '(none)'}")
        for t in s.get("thresholds", []):
            lines.append(f"- **Target**: {t.get('target')}% ({t.get('timeframe')})")
        lines.append("")
    return "\n".join(lines)


async def list_slos(params: PaginatedInput) -> str:
    """List Datadog SLOs with current status and error budget info."""
    try:
        data = await api_request("slo", "v1")
        return format_output(data, params.response_format, _slos_md)
    except Exception as exc:
        return handle_error(exc)


async def get_slo(params: SloGetInput) -> str:
    """Get detailed configuration for a specific SLO."""
    try:
        data = await api_request(f"slo/{params.slo_id}", "v1")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def delete_slo(params: SloDeleteInput) -> str:
    """Permanently delete a Datadog SLO."""
    try:
        await api_request(f"slo/{params.slo_id}", "v1", method="DELETE")
        return f"SLO {params.slo_id} deleted successfully."
    except Exception as exc:
        return handle_error(exc)
