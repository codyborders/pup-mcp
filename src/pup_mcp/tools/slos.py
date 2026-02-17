"""Datadog SLO management tools: list, get, create, update, delete, corrections."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class SloGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class SloCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, description="SLO name")
    slo_type: str = Field(
        ..., alias="slo_type",
        description="SLO type: metric, monitor, or time_slice",
    )
    thresholds: List[Dict[str, Any]] = Field(
        ..., min_length=1,
        description="Thresholds with target, timeframe, and optional warning",
    )
    description: Optional[str] = Field(default=None, description="SLO description")
    tags: Optional[List[str]] = Field(default=None, description="Tags list")
    monitor_ids: Optional[List[int]] = Field(
        default=None, description="Monitor IDs (required for monitor type)",
    )
    query: Optional[Dict[str, str]] = Field(
        default=None,
        description="Metric query with numerator and denominator (for metric type)",
    )


class SloUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID to update")
    name: str = Field(..., min_length=1, description="SLO name")
    slo_type: str = Field(..., description="SLO type: metric, monitor, or time_slice")
    thresholds: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="Thresholds",
    )
    description: Optional[str] = Field(default=None, description="SLO description")
    tags: Optional[List[str]] = Field(default=None, description="Tags list")
    monitor_ids: Optional[List[int]] = Field(default=None, description="Monitor IDs")
    query: Optional[Dict[str, str]] = Field(default=None, description="Metric query")


class SloDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID to delete")


class SloCorrectionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

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


def _corrections_md(data: Any) -> str:
    corrections: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    if not corrections:
        return "No corrections found."
    lines = [f"# SLO Corrections ({len(corrections)})", ""]
    for c in corrections:
        attrs = c.get("attributes", {})
        lines.append(f"## {c.get('id', '?')}")
        lines.append(f"- **Category**: {attrs.get('category', '?')}")
        lines.append(f"- **Description**: {attrs.get('description', '(none)')}")
        start = attrs.get("start")
        end = attrs.get("end")
        if start:
            lines.append(f"- **Start**: {datetime.fromtimestamp(start, tz=timezone.utc).isoformat()}")
        if end:
            lines.append(f"- **End**: {datetime.fromtimestamp(end, tz=timezone.utc).isoformat()}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper to build SLO request body
# ---------------------------------------------------------------------------

def _slo_body(
    name: str,
    slo_type: str,
    thresholds: List[Dict[str, Any]],
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    monitor_ids: Optional[List[int]] = None,
    query: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Build the JSON body for create/update SLO requests."""
    body: Dict[str, Any] = {
        "name": name,
        "type": slo_type,
        "thresholds": thresholds,
    }
    if description is not None:
        body["description"] = description
    if tags is not None:
        body["tags"] = tags
    if monitor_ids is not None:
        body["monitor_ids"] = monitor_ids
    if query is not None:
        body["query"] = query
    return body


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

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


async def create_slo(params: SloCreateInput) -> str:
    """Create a new SLO."""
    try:
        body = _slo_body(
            name=params.name,
            slo_type=params.slo_type,
            thresholds=params.thresholds,
            description=params.description,
            tags=params.tags,
            monitor_ids=params.monitor_ids,
            query=params.query,
        )
        data = await api_request("slo", "v1", method="POST", json_body=body)
        slo_list = data.get("data", []) if isinstance(data, dict) else []
        slo_id = slo_list[0].get("id", "unknown") if slo_list else "unknown"
        return f"SLO '{params.name}' created successfully (id={slo_id})."
    except Exception as exc:
        return handle_error(exc)


async def update_slo(params: SloUpdateInput) -> str:
    """Update an existing SLO (full replacement)."""
    try:
        body = _slo_body(
            name=params.name,
            slo_type=params.slo_type,
            thresholds=params.thresholds,
            description=params.description,
            tags=params.tags,
            monitor_ids=params.monitor_ids,
            query=params.query,
        )
        await api_request(f"slo/{params.slo_id}", "v1", method="PUT", json_body=body)
        return f"SLO {params.slo_id} updated successfully."
    except Exception as exc:
        return handle_error(exc)


async def delete_slo(params: SloDeleteInput) -> str:
    """Permanently delete a Datadog SLO."""
    try:
        await api_request(f"slo/{params.slo_id}", "v1", method="DELETE")
        return f"SLO {params.slo_id} deleted successfully."
    except Exception as exc:
        return handle_error(exc)


async def get_slo_corrections(params: SloCorrectionsInput) -> str:
    """Get status corrections for an SLO."""
    try:
        data = await api_request(f"slo/{params.slo_id}/corrections", "v1")
        return format_output(data, params.response_format, _corrections_md)
    except Exception as exc:
        return handle_error(exc)
