"""MCP Server for Datadog (pup CLI).

Provides tools to interact with the Datadog API, mirroring the capabilities
of the pup CLI: monitors, dashboards, metrics, logs, events, incidents,
SLOs, synthetics, downtimes, hosts/tags, and users.
"""

import json
import os
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHARACTER_LIMIT = 25_000
DEFAULT_SITE = "datadoghq.com"
API_TIMEOUT = 30.0
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
mcp = FastMCP("pup_mcp")


# ---------------------------------------------------------------------------
# Shared enums / models
# ---------------------------------------------------------------------------
class ResponseFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


class PaginatedInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip for pagination")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' for structured data or 'markdown' for human-readable",
    )


# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------
def _get_config() -> Dict[str, str]:
    api_key = os.environ.get("DD_API_KEY", "")
    app_key = os.environ.get("DD_APP_KEY", "")
    site = os.environ.get("DD_SITE", DEFAULT_SITE)
    if not api_key or not app_key:
        raise ValueError(
            "DD_API_KEY and DD_APP_KEY environment variables are required. "
            "Set them before starting the server."
        )
    return {"api_key": api_key, "app_key": app_key, "site": site}


def _base_url(version: str = "v1") -> str:
    cfg = _get_config()
    return f"https://api.{cfg['site']}/api/{version}"


def _headers() -> Dict[str, str]:
    cfg = _get_config()
    return {
        "DD-API-KEY": cfg["api_key"],
        "DD-APPLICATION-KEY": cfg["app_key"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _api_request(
    endpoint: str,
    version: str = "v1",
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
) -> Any:
    url = f"{_base_url(version)}/{endpoint}"
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.request(
            method, url, headers=_headers(), params=params, json=json_body
        )
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()


def _handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text
        messages: Dict[int, str] = {
            400: "Bad request. Check your parameters.",
            401: "Unauthorized. Check that DD_API_KEY and DD_APP_KEY are valid.",
            403: "Forbidden. Your API key lacks permission for this operation.",
            404: "Resource not found. Check the ID is correct.",
            429: "Rate limit exceeded. Wait before retrying.",
        }
        msg = messages.get(status, f"Datadog API returned status {status}.")
        return f"Error: {msg}\n{json.dumps(body, indent=2) if isinstance(body, dict) else body}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Try again."
    if isinstance(e, httpx.ConnectError):
        return "Error: Could not reach Datadog API. Check DD_SITE and network."
    if isinstance(e, ValueError):
        return f"Error: {e}"
    return f"Error: {type(e).__name__}: {e}"


def _truncate(text: str) -> str:
    if len(text) <= CHARACTER_LIMIT:
        return text
    return text[:CHARACTER_LIMIT] + "\n\n[Truncated. Use pagination or filters to narrow results.]"


def _fmt(data: Any, fmt: ResponseFormat, md_fn: Any = None) -> str:
    if fmt == ResponseFormat.MARKDOWN and md_fn:
        return _truncate(md_fn(data))
    return _truncate(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Time parsing (mirrors pup's relative time support)
# ---------------------------------------------------------------------------
_RELATIVE_RE = re.compile(r"^(\d+)([smhdw])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def _parse_time(value: str) -> int:
    """Parse a time string to Unix seconds. Supports relative (1h, 30m, 7d) and absolute."""
    if re.match(r"^\d{10,}$", value):
        return int(value)
    m = _RELATIVE_RE.match(value)
    if m:
        return int(time.time()) - int(m.group(1)) * _UNIT_SECONDS[m.group(2)]
    parsed = None
    try:
        from datetime import datetime, timezone

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        pass
    if parsed:
        return int(parsed.timestamp())
    raise ValueError(f"Invalid time: '{value}'. Use relative (1h, 30m, 7d) or absolute (Unix, RFC3339).")


# ============================= MONITORS ====================================


class MonitorsListInput(PaginatedInput):
    name: Optional[str] = Field(default=None, description="Filter by monitor name substring")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags (e.g. 'env:prod,team:backend')")


class MonitorGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monitor_id: int = Field(..., gt=0, description="Numeric monitor ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class MonitorsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, description="Search query (e.g. 'type:metric status:alert')")
    page: int = Field(default=0, ge=0, description="Page number")
    per_page: int = Field(default=30, ge=1, le=100, description="Results per page")
    sort: Optional[str] = Field(default=None, description="Sort specification (e.g. 'name,asc')")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class MonitorDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monitor_id: int = Field(..., gt=0, description="Numeric monitor ID to delete")


@mcp.tool(
    name="pup_monitors_list",
    annotations={"title": "List Monitors", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_monitors_list(params: MonitorsListInput) -> str:
    """List Datadog monitors with optional name/tag filtering and pagination.

    Returns monitor id, name, type, overall_state, and tags for each match.
    """
    try:
        qp: Dict[str, Any] = {"page_size": params.limit, "page": params.offset // params.limit}
        if params.name:
            qp["name"] = params.name
        if params.tags:
            qp["monitor_tags"] = params.tags
        data = await _api_request("monitor", "v1", params=qp)

        def _md(d: Any) -> str:
            monitors = d if isinstance(d, list) else []
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

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_monitors_get",
    annotations={"title": "Get Monitor", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_monitors_get(params: MonitorGetInput) -> str:
    """Get detailed configuration for a specific Datadog monitor by ID.

    Returns the full monitor definition including query, thresholds, message, and tags.
    """
    try:
        data = await _api_request(f"monitor/{params.monitor_id}", "v1")

        def _md(d: Any) -> str:
            m = d
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

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_monitors_search",
    annotations={"title": "Search Monitors", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_monitors_search(params: MonitorsSearchInput) -> str:
    """Search Datadog monitors using query syntax (e.g. 'type:metric status:alert').

    Supports pagination and sorting. Returns matching monitors with metadata.
    """
    try:
        qp: Dict[str, Any] = {"query": params.query, "page": params.page, "per_page": params.per_page}
        if params.sort:
            qp["sort"] = params.sort
        data = await _api_request("monitor/search", "v1", params=qp)
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_monitors_delete",
    annotations={"title": "Delete Monitor", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
)
async def pup_monitors_delete(params: MonitorDeleteInput) -> str:
    """Permanently delete a Datadog monitor by ID. This cannot be undone."""
    try:
        await _api_request(f"monitor/{params.monitor_id}", "v1", method="DELETE")
        return f"Monitor {params.monitor_id} deleted successfully."
    except Exception as e:
        return _handle_error(e)


# ============================= DASHBOARDS ==================================


class DashboardGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dashboard_id: str = Field(..., min_length=1, description="Dashboard ID (e.g. 'abc-def-ghi')")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class DashboardDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dashboard_id: str = Field(..., min_length=1, description="Dashboard ID to delete")


@mcp.tool(
    name="pup_dashboards_list",
    annotations={"title": "List Dashboards", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_dashboards_list(params: PaginatedInput) -> str:
    """List all dashboards in your Datadog account.

    Returns dashboard id, title, description, author, and URL for each dashboard.
    """
    try:
        data = await _api_request("dashboard", "v1")

        def _md(d: Any) -> str:
            dashboards = d.get("dashboards", []) if isinstance(d, dict) else []
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

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_dashboards_get",
    annotations={"title": "Get Dashboard", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_dashboards_get(params: DashboardGetInput) -> str:
    """Get full configuration for a Datadog dashboard including widgets, template variables, and layout."""
    try:
        data = await _api_request(f"dashboard/{params.dashboard_id}", "v1")

        def _md(d: Any) -> str:
            db = d
            widgets = db.get("widgets", [])
            lines = [
                f"# Dashboard: {db.get('title')}",
                "",
                f"- **ID**: {db.get('id')}",
                f"- **Layout**: {db.get('layout_type')}",
                f"- **Widgets**: {len(widgets)}",
                f"- **Description**: {db.get('description') or '(none)'}",
                f"- **Author**: {db.get('author_handle', 'unknown')}",
                f"- **Created**: {db.get('created_at')}",
                f"- **Modified**: {db.get('modified_at')}",
            ]
            return "\n".join(lines)

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_dashboards_delete",
    annotations={"title": "Delete Dashboard", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
)
async def pup_dashboards_delete(params: DashboardDeleteInput) -> str:
    """Permanently delete a Datadog dashboard. This cannot be undone."""
    try:
        await _api_request(f"dashboard/{params.dashboard_id}", "v1", method="DELETE")
        return f"Dashboard {params.dashboard_id} deleted successfully."
    except Exception as e:
        return _handle_error(e)


# ============================= METRICS =====================================


class MetricsQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, description="Metrics query (e.g. 'avg:system.cpu.user{*}')")
    from_time: str = Field(default="1h", alias="from", description="Start time: relative (1h, 30m, 7d) or absolute")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time (default: now)")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class MetricsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, description="Metric name search string")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class MetricsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filter_string: Optional[str] = Field(default=None, alias="filter", description="Filter metrics by name pattern")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class MetricSubmitInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric: str = Field(..., min_length=1, description="Metric name (e.g. 'custom.my_metric')")
    value: float = Field(..., description="Metric value")
    metric_type: str = Field(default="gauge", description="Type: gauge, count, or rate")
    tags: Optional[List[str]] = Field(default=None, description="Tags (e.g. ['env:prod', 'team:backend'])")
    host: Optional[str] = Field(default=None, description="Host name")


@mcp.tool(
    name="pup_metrics_query",
    annotations={"title": "Query Metrics", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_metrics_query(params: MetricsQueryInput) -> str:
    """Query Datadog time-series metrics.

    Supports aggregation syntax like 'avg:system.cpu.user{*}' with relative or absolute time ranges.
    """
    try:
        from_ts = _parse_time(params.from_time)
        to_ts = _parse_time(params.to_time) if params.to_time else int(time.time())
        qp = {"query": params.query, "from": from_ts, "to": to_ts}
        data = await _api_request("query", "v1", params=qp)
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_metrics_search",
    annotations={"title": "Search Metrics", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_metrics_search(params: MetricsSearchInput) -> str:
    """Search for metric names matching a query string."""
    try:
        data = await _api_request("search", "v1", params={"q": f"metrics:{params.query}"})
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_metrics_list",
    annotations={"title": "List Metrics", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_metrics_list(params: MetricsListInput) -> str:
    """List available metrics, optionally filtered by name pattern."""
    try:
        from_ts = int(time.time()) - 3600
        qp: Dict[str, Any] = {"from": from_ts}
        if params.filter_string:
            qp["filter[tags]"] = params.filter_string
        data = await _api_request("metrics", "v1", params=qp)
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_metrics_submit",
    annotations={"title": "Submit Metric", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
)
async def pup_metrics_submit(params: MetricSubmitInput) -> str:
    """Submit a custom metric data point to Datadog.

    Args:
        metric: Metric name (e.g. 'custom.my_metric')
        value: Numeric value
        metric_type: gauge, count, or rate
        tags: Optional list of tags
        host: Optional host name
    """
    try:
        point = {"metric": params.metric, "type": params.metric_type, "points": [[int(time.time()), params.value]]}
        if params.tags:
            point["tags"] = params.tags
        if params.host:
            point["host"] = params.host
        body = {"series": [point]}
        await _api_request("series", "v1", method="POST", json_body=body)
        return f"Metric '{params.metric}' submitted successfully (value={params.value})."
    except Exception as e:
        return _handle_error(e)


# ============================= LOGS ========================================


class LogsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(default="*", description="Log search query (Datadog query syntax)")
    from_time: str = Field(default="1h", alias="from", description="Start time: relative or absolute")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time (default: now)")
    limit: int = Field(default=20, ge=1, le=1000, description="Max log entries to return")
    sort: str = Field(default="desc", description="Sort order: 'asc' or 'desc'")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


@mcp.tool(
    name="pup_logs_search",
    annotations={"title": "Search Logs", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_logs_search(params: LogsSearchInput) -> str:
    """Search Datadog logs using query syntax with time range and pagination.

    Supports the full Datadog log query language. Returns matching log entries
    with timestamp, status, service, and message.
    """
    try:
        from_ts = _parse_time(params.from_time)
        to_ts = _parse_time(params.to_time) if params.to_time else int(time.time())
        from_ms = from_ts * 1000
        to_ms = to_ts * 1000
        body = {
            "filter": {"query": params.query, "from": f"{from_ms}", "to": f"{to_ms}"},
            "sort": f"timestamp" if params.sort == "asc" else "-timestamp",
            "page": {"limit": params.limit},
        }
        data = await _api_request("logs/events/search", "v2", method="POST", json_body=body)

        def _md(d: Any) -> str:
            logs = d.get("data", []) if isinstance(d, dict) else []
            if not logs:
                return "No log entries found."
            lines = [f"# Logs ({len(logs)} entries)", ""]
            for entry in logs:
                attrs = entry.get("attributes", {})
                lines.append(f"**[{attrs.get('timestamp', '?')}]** `{attrs.get('status', '?')}` {attrs.get('service', '?')}")
                lines.append(f"  {attrs.get('message', '(no message)')}")
                lines.append("")
            return "\n".join(lines)

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


# ============================= EVENTS ======================================


class EventsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_time: str = Field(default="1h", alias="from", description="Start time: relative or absolute")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time (default: now)")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags to filter by")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class EventsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(default="*", description="Event search query")
    from_time: str = Field(default="1h", alias="from", description="Start time")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class EventGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(..., min_length=1, description="Event ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


@mcp.tool(
    name="pup_events_list",
    annotations={"title": "List Events", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_events_list(params: EventsListInput) -> str:
    """List recent Datadog events within a time range, optionally filtered by tags."""
    try:
        from_ts = _parse_time(params.from_time)
        to_ts = _parse_time(params.to_time) if params.to_time else int(time.time())
        qp: Dict[str, Any] = {"start": from_ts, "end": to_ts}
        if params.tags:
            qp["tags"] = params.tags
        data = await _api_request("events", "v1", params=qp)
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_events_search",
    annotations={"title": "Search Events", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_events_search(params: EventsSearchInput) -> str:
    """Search Datadog events using query syntax with time range filtering."""
    try:
        from_ts = _parse_time(params.from_time)
        to_ts = _parse_time(params.to_time) if params.to_time else int(time.time())
        body = {
            "filter": {"query": params.query, "from": f"{from_ts}", "to": f"{to_ts}"},
            "page": {"limit": params.limit},
        }
        data = await _api_request("events/search", "v2", method="POST", json_body=body)
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_events_get",
    annotations={"title": "Get Event", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_events_get(params: EventGetInput) -> str:
    """Get details for a specific Datadog event by ID."""
    try:
        data = await _api_request(f"events/{params.event_id}", "v1")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


# ============================= INCIDENTS ===================================


class IncidentsListInput(PaginatedInput):
    pass


class IncidentGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str = Field(..., min_length=1, description="Incident ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


@mcp.tool(
    name="pup_incidents_list",
    annotations={"title": "List Incidents", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_incidents_list(params: IncidentsListInput) -> str:
    """List Datadog incidents with pagination.

    Returns incident id, title, status, severity, and timestamps.
    """
    try:
        qp: Dict[str, Any] = {"page[size]": params.limit, "page[offset]": params.offset}
        data = await _api_request("incidents", "v2", params=qp)

        def _md(d: Any) -> str:
            incidents = d.get("data", []) if isinstance(d, dict) else []
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

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_incidents_get",
    annotations={"title": "Get Incident", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_incidents_get(params: IncidentGetInput) -> str:
    """Get detailed information for a specific Datadog incident including timeline and tasks."""
    try:
        data = await _api_request(f"incidents/{params.incident_id}", "v2")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


# ============================= SLOs ========================================


class SloGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class SloDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slo_id: str = Field(..., min_length=1, description="SLO ID to delete")


@mcp.tool(
    name="pup_slos_list",
    annotations={"title": "List SLOs", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_slos_list(params: PaginatedInput) -> str:
    """List Datadog Service Level Objectives with current status and error budget info."""
    try:
        data = await _api_request("slo", "v1")

        def _md(d: Any) -> str:
            slos = d.get("data", []) if isinstance(d, dict) else []
            if not slos:
                return "No SLOs found."
            lines = [f"# SLOs ({len(slos)})", ""]
            for s in slos:
                lines.append(f"## {s.get('name', '?')} ({s.get('id')})")
                lines.append(f"- **Type**: {s.get('type')}")
                lines.append(f"- **Description**: {s.get('description') or '(none)'}")
                thresholds = s.get("thresholds", [])
                for t in thresholds:
                    lines.append(f"- **Target**: {t.get('target')}% ({t.get('timeframe')})")
                lines.append("")
            return "\n".join(lines)

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_slos_get",
    annotations={"title": "Get SLO", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_slos_get(params: SloGetInput) -> str:
    """Get detailed configuration and status for a specific SLO by ID."""
    try:
        data = await _api_request(f"slo/{params.slo_id}", "v1")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_slos_delete",
    annotations={"title": "Delete SLO", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
)
async def pup_slos_delete(params: SloDeleteInput) -> str:
    """Permanently delete a Datadog SLO. This cannot be undone."""
    try:
        await _api_request(f"slo/{params.slo_id}", "v1", method="DELETE")
        return f"SLO {params.slo_id} deleted successfully."
    except Exception as e:
        return _handle_error(e)


# ============================= SYNTHETICS ==================================


class SyntheticsTestGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    test_id: str = Field(..., min_length=1, description="Synthetic test public ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class SyntheticsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Optional[str] = Field(default=None, description="Search text to filter tests")
    count: int = Field(default=50, ge=1, le=100, description="Number of results")
    start: int = Field(default=0, ge=0, description="Offset for pagination")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


@mcp.tool(
    name="pup_synthetics_tests_list",
    annotations={"title": "List Synthetic Tests", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_synthetics_tests_list(params: PaginatedInput) -> str:
    """List all Datadog synthetic monitoring tests."""
    try:
        data = await _api_request("synthetics/tests", "v1")

        def _md(d: Any) -> str:
            tests = d.get("tests", []) if isinstance(d, dict) else []
            if not tests:
                return "No synthetic tests found."
            lines = [f"# Synthetic Tests ({len(tests)})", ""]
            for t in tests:
                lines.append(f"## {t.get('name', '?')} ({t.get('public_id')})")
                lines.append(f"- **Type**: {t.get('type')}")
                lines.append(f"- **Status**: {t.get('status')}")
                lines.append("")
            return "\n".join(lines)

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_synthetics_tests_get",
    annotations={"title": "Get Synthetic Test", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_synthetics_tests_get(params: SyntheticsTestGetInput) -> str:
    """Get detailed configuration for a specific synthetic test by public ID."""
    try:
        data = await _api_request(f"synthetics/tests/{params.test_id}", "v1")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_synthetics_tests_search",
    annotations={"title": "Search Synthetic Tests", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_synthetics_tests_search(params: SyntheticsSearchInput) -> str:
    """Search synthetic tests with optional text filter and pagination."""
    try:
        qp: Dict[str, Any] = {"count": params.count, "start": params.start}
        if params.text:
            qp["text"] = params.text
        data = await _api_request("synthetics/tests/search", "v1", params=qp)
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_synthetics_locations_list",
    annotations={"title": "List Synthetic Locations", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_synthetics_locations_list() -> str:
    """List available Datadog synthetic monitoring locations/regions."""
    try:
        data = await _api_request("synthetics/locations", "v1")
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return _handle_error(e)


# ============================= DOWNTIMES ===================================


class DowntimeGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    downtime_id: str = Field(..., min_length=1, description="Downtime ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class DowntimeCancelInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    downtime_id: str = Field(..., min_length=1, description="Downtime ID to cancel")


@mcp.tool(
    name="pup_downtimes_list",
    annotations={"title": "List Downtimes", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_downtimes_list(params: PaginatedInput) -> str:
    """List all scheduled downtimes in your Datadog account."""
    try:
        data = await _api_request("downtime", "v2")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_downtimes_get",
    annotations={"title": "Get Downtime", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_downtimes_get(params: DowntimeGetInput) -> str:
    """Get details for a specific downtime by ID."""
    try:
        data = await _api_request(f"downtime/{params.downtime_id}", "v2")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_downtimes_cancel",
    annotations={"title": "Cancel Downtime", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
)
async def pup_downtimes_cancel(params: DowntimeCancelInput) -> str:
    """Cancel a scheduled downtime by ID."""
    try:
        await _api_request(f"downtime/{params.downtime_id}", "v2", method="DELETE")
        return f"Downtime {params.downtime_id} cancelled successfully."
    except Exception as e:
        return _handle_error(e)


# ============================= HOSTS / TAGS ================================


class TagsGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str = Field(..., min_length=1, description="Hostname")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class TagsModifyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str = Field(..., min_length=1, description="Hostname")
    tags: List[str] = Field(..., min_length=1, description="Tags to add/set (e.g. ['env:prod', 'role:web'])")


class TagsDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str = Field(..., min_length=1, description="Hostname to remove all tags from")


@mcp.tool(
    name="pup_tags_list",
    annotations={"title": "List Host Tags", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_tags_list(params: PaginatedInput) -> str:
    """List all host tags across your Datadog infrastructure."""
    try:
        data = await _api_request("tags/hosts", "v1")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_tags_get",
    annotations={"title": "Get Host Tags", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_tags_get(params: TagsGetInput) -> str:
    """Get all tags for a specific host."""
    try:
        data = await _api_request(f"tags/hosts/{params.host}", "v1")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_tags_add",
    annotations={"title": "Add Host Tags", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
)
async def pup_tags_add(params: TagsModifyInput) -> str:
    """Add tags to a host."""
    try:
        body = {"tags": params.tags}
        data = await _api_request(f"tags/hosts/{params.host}", "v1", method="POST", json_body=body)
        return _fmt(data, ResponseFormat.JSON)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_tags_update",
    annotations={"title": "Update Host Tags", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_tags_update(params: TagsModifyInput) -> str:
    """Replace all tags on a host with the provided list."""
    try:
        body = {"tags": params.tags}
        data = await _api_request(f"tags/hosts/{params.host}", "v1", method="PUT", json_body=body)
        return _fmt(data, ResponseFormat.JSON)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_tags_delete",
    annotations={"title": "Delete Host Tags", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True},
)
async def pup_tags_delete(params: TagsDeleteInput) -> str:
    """Delete all tags from a host."""
    try:
        await _api_request(f"tags/hosts/{params.host}", "v1", method="DELETE")
        return f"All tags deleted from host '{params.host}'."
    except Exception as e:
        return _handle_error(e)


# ============================= USERS =======================================


class UserGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(..., min_length=1, description="User ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


@mcp.tool(
    name="pup_users_list",
    annotations={"title": "List Users", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_users_list(params: PaginatedInput) -> str:
    """List users in your Datadog organization."""
    try:
        data = await _api_request("user", "v1")

        def _md(d: Any) -> str:
            users = d.get("users", []) if isinstance(d, dict) else []
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

        return _fmt(data, params.response_format, _md)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_users_get",
    annotations={"title": "Get User", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_users_get(params: UserGetInput) -> str:
    """Get details for a specific Datadog user by ID."""
    try:
        data = await _api_request(f"user/{params.user_id}", "v1")
        return _fmt(data, params.response_format)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pup_roles_list",
    annotations={"title": "List Roles", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def pup_roles_list() -> str:
    """List available roles in your Datadog organization."""
    try:
        data = await _api_request("roles", "v2")
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return _handle_error(e)


# ============================= ENTRY POINT =================================

if __name__ == "__main__":
    mcp.run()
