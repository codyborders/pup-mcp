"""Datadog RUM (Real User Monitoring) tools.

Covers applications, metrics, retention filters, sessions, playlists,
and heatmaps via the Datadog v2 API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output
from pup_mcp.utils.time_parser import now_unix, parse_time


# ---------------------------------------------------------------------------
# Input models -- Applications
# ---------------------------------------------------------------------------

class RumAppsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumAppGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumAppCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, description="Application name")
    app_type: str = Field(
        ..., alias="type",
        description="Application type: browser, ios, android, react-native, or flutter",
    )


class RumAppUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")
    name: Optional[str] = Field(default=None, description="New application name")
    app_type: Optional[str] = Field(default=None, alias="type", description="New application type")


class RumAppDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")


# ---------------------------------------------------------------------------
# Input models -- Metrics
# ---------------------------------------------------------------------------

class RumMetricsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumMetricGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_id: str = Field(..., min_length=1, description="RUM metric ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumMetricCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, description="Metric name")
    event_type: str = Field(
        ..., description="RUM event type: views, actions, errors, resources, or longTasks",
    )
    compute_type: str = Field(default="count", description="Aggregation type: count, distribution")
    filter_query: Optional[str] = Field(default=None, alias="filter", description="Filter query")
    group_by: Optional[List[str]] = Field(default=None, description="Group-by paths")


class RumMetricUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_id: str = Field(..., min_length=1, description="RUM metric ID")
    compute_type: Optional[str] = Field(default=None, description="Aggregation type")
    filter_query: Optional[str] = Field(default=None, alias="filter", description="Filter query")
    group_by: Optional[List[str]] = Field(default=None, description="Group-by paths")


class RumMetricDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_id: str = Field(..., min_length=1, description="RUM metric ID")


# ---------------------------------------------------------------------------
# Input models -- Retention Filters
# ---------------------------------------------------------------------------

class RumRetentionFiltersListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumRetentionFilterGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")
    filter_id: str = Field(..., min_length=1, description="Retention filter ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumRetentionFilterCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")
    name: str = Field(..., min_length=1, description="Filter name")
    query: str = Field(default="*", description="Filter query")
    rate: int = Field(default=100, ge=0, le=100, description="Sample rate (0-100)")
    filter_type: str = Field(default="session-replay", alias="type", description="Filter type")
    enabled: bool = Field(default=True, description="Whether filter is enabled")


class RumRetentionFilterUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")
    filter_id: str = Field(..., min_length=1, description="Retention filter ID")
    name: Optional[str] = Field(default=None, description="New filter name")
    query: Optional[str] = Field(default=None, description="New filter query")
    rate: Optional[int] = Field(default=None, ge=0, le=100, description="New sample rate")
    enabled: Optional[bool] = Field(default=None, description="Enable or disable")


class RumRetentionFilterDeleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_id: str = Field(..., min_length=1, description="RUM application ID")
    filter_id: str = Field(..., min_length=1, description="Retention filter ID")


# ---------------------------------------------------------------------------
# Input models -- Sessions
# ---------------------------------------------------------------------------

class RumSessionsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_time: str = Field(default="1h", alias="from", description="Start time (relative or absolute)")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time (default: now)")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumSessionsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, description="RUM search query (e.g. '@type:view')")
    from_time: str = Field(default="1h", alias="from", description="Start time")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time (default: now)")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


# ---------------------------------------------------------------------------
# Input models -- Playlists
# ---------------------------------------------------------------------------

class RumPlaylistsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class RumPlaylistGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    playlist_id: str = Field(..., min_length=1, description="Playlist ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


# ---------------------------------------------------------------------------
# Input models -- Heatmaps
# ---------------------------------------------------------------------------

class RumHeatmapQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    view: str = Field(..., min_length=1, description="View/page name to query")
    from_time: str = Field(default="24h", alias="from", description="Start time")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time (default: now)")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def _apps_md(data: Any) -> str:
    apps: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    if not apps:
        return "No RUM applications found."
    lines = [f"# RUM Applications ({len(apps)})", ""]
    for app in apps:
        attrs = app.get("attributes", {})
        lines.append(f"## {attrs.get('name', '?')} ({app.get('id', '?')})")
        lines.append(f"- **Type**: {attrs.get('type', '?')}")
        lines.append(f"- **Created**: {attrs.get('created_at', '?')}")
        lines.append("")
    return "\n".join(lines)


def _metrics_md(data: Any) -> str:
    metrics: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    if not metrics:
        return "No RUM metrics found."
    lines = [f"# RUM Metrics ({len(metrics)})", ""]
    for m in metrics:
        attrs = m.get("attributes", {})
        lines.append(f"## {attrs.get('path', m.get('id', '?'))}")
        lines.append(f"- **Event Type**: {attrs.get('event_type', '?')}")
        lines.append(f"- **Compute**: {attrs.get('compute', {}).get('aggregation_type', '?')}")
        lines.append("")
    return "\n".join(lines)


def _sessions_md(data: Any) -> str:
    events: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    if not events:
        return "No RUM sessions found."
    lines = [f"# RUM Sessions ({len(events)})", ""]
    for ev in events:
        attrs = ev.get("attributes", {})
        lines.append(f"**[{attrs.get('timestamp', '?')}]** {attrs.get('service', '?')}")
        session = attrs.get("session", {})
        lines.append(f"  Session: {session.get('id', '?')} | Type: {attrs.get('type', '?')}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool functions -- Applications
# ---------------------------------------------------------------------------

async def rum_apps_list(params: RumAppsListInput) -> str:
    """List all RUM applications."""
    try:
        data = await api_request("rum/applications", "v2")
        return format_output(data, params.response_format, _apps_md)
    except Exception as exc:
        return handle_error(exc)


async def rum_app_get(params: RumAppGetInput) -> str:
    """Get details for a specific RUM application."""
    try:
        data = await api_request(f"rum/applications/{params.app_id}", "v2")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def rum_app_create(params: RumAppCreateInput) -> str:
    """Create a new RUM application."""
    try:
        body = {
            "data": {
                "attributes": {"name": params.name, "type": params.app_type},
                "type": "rum_application_create",
            }
        }
        data = await api_request(
            "rum/applications", "v2", method="POST", json_body=body,
        )
        app_id = data.get("data", {}).get("id", "unknown") if isinstance(data, dict) else "unknown"
        return f"RUM application '{params.name}' created successfully (id={app_id})."
    except Exception as exc:
        return handle_error(exc)


async def rum_app_update(params: RumAppUpdateInput) -> str:
    """Update an existing RUM application."""
    try:
        attrs: Dict[str, Any] = {}
        if params.name is not None:
            attrs["name"] = params.name
        if params.app_type is not None:
            attrs["type"] = params.app_type
        body = {
            "data": {
                "attributes": attrs,
                "id": params.app_id,
                "type": "rum_application_update",
            }
        }
        data = await api_request(
            f"rum/applications/{params.app_id}", "v2", method="PATCH", json_body=body,
        )
        return format_output(data, ResponseFormat.JSON)
    except Exception as exc:
        return handle_error(exc)


async def rum_app_delete(params: RumAppDeleteInput) -> str:
    """Delete a RUM application."""
    try:
        await api_request(f"rum/applications/{params.app_id}", "v2", method="DELETE")
        return f"RUM application {params.app_id} deleted successfully."
    except Exception as exc:
        return handle_error(exc)


# ---------------------------------------------------------------------------
# Tool functions -- Metrics
# ---------------------------------------------------------------------------

async def rum_metrics_list(params: RumMetricsListInput) -> str:
    """List all RUM-based metrics."""
    try:
        data = await api_request("rum/metrics", "v2")
        return format_output(data, params.response_format, _metrics_md)
    except Exception as exc:
        return handle_error(exc)


async def rum_metric_get(params: RumMetricGetInput) -> str:
    """Get details for a specific RUM metric."""
    try:
        data = await api_request(f"rum/metrics/{params.metric_id}", "v2")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def rum_metric_create(params: RumMetricCreateInput) -> str:
    """Create a new RUM-based metric."""
    try:
        attrs: Dict[str, Any] = {
            "event_type": params.event_type,
            "compute": {"aggregation_type": params.compute_type},
        }
        if params.filter_query:
            attrs["filter"] = {"query": params.filter_query}
        if params.group_by:
            attrs["group_by"] = [{"path": p} for p in params.group_by]
        body = {
            "data": {
                "attributes": attrs,
                "id": params.name,
                "type": "rum_metrics",
            }
        }
        await api_request("rum/metrics", "v2", method="POST", json_body=body)
        return f"RUM metric '{params.name}' created successfully."
    except Exception as exc:
        return handle_error(exc)


async def rum_metric_update(params: RumMetricUpdateInput) -> str:
    """Update an existing RUM metric."""
    try:
        attrs: Dict[str, Any] = {}
        if params.compute_type is not None:
            attrs["compute"] = {"aggregation_type": params.compute_type}
        if params.filter_query is not None:
            attrs["filter"] = {"query": params.filter_query}
        if params.group_by is not None:
            attrs["group_by"] = [{"path": p} for p in params.group_by]
        body = {
            "data": {
                "attributes": attrs,
                "id": params.metric_id,
                "type": "rum_metrics",
            }
        }
        await api_request(
            f"rum/metrics/{params.metric_id}", "v2", method="PATCH", json_body=body,
        )
        return f"RUM metric '{params.metric_id}' updated successfully."
    except Exception as exc:
        return handle_error(exc)


async def rum_metric_delete(params: RumMetricDeleteInput) -> str:
    """Delete a RUM metric."""
    try:
        await api_request(f"rum/metrics/{params.metric_id}", "v2", method="DELETE")
        return f"RUM metric '{params.metric_id}' deleted successfully."
    except Exception as exc:
        return handle_error(exc)


# ---------------------------------------------------------------------------
# Tool functions -- Retention Filters
# ---------------------------------------------------------------------------

async def rum_retention_filters_list(params: RumRetentionFiltersListInput) -> str:
    """List retention filters for a RUM application."""
    try:
        data = await api_request(
            f"rum/applications/{params.app_id}/retention_filters", "v2",
        )
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def rum_retention_filter_get(params: RumRetentionFilterGetInput) -> str:
    """Get a specific retention filter for a RUM application."""
    try:
        data = await api_request(
            f"rum/applications/{params.app_id}/retention_filters/{params.filter_id}", "v2",
        )
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def rum_retention_filter_create(params: RumRetentionFilterCreateInput) -> str:
    """Create a retention filter for a RUM application."""
    try:
        body = {
            "data": {
                "attributes": {
                    "name": params.name,
                    "event_type": params.filter_type,
                    "query": params.query,
                    "sample_rate": params.rate,
                    "enabled": params.enabled,
                },
                "type": "retention_filters",
            }
        }
        await api_request(
            f"rum/applications/{params.app_id}/retention_filters", "v2",
            method="POST", json_body=body,
        )
        return f"Retention filter '{params.name}' created successfully."
    except Exception as exc:
        return handle_error(exc)


async def rum_retention_filter_update(params: RumRetentionFilterUpdateInput) -> str:
    """Update a retention filter for a RUM application."""
    try:
        attrs: Dict[str, Any] = {}
        if params.name is not None:
            attrs["name"] = params.name
        if params.query is not None:
            attrs["query"] = params.query
        if params.rate is not None:
            attrs["sample_rate"] = params.rate
        if params.enabled is not None:
            attrs["enabled"] = params.enabled
        body = {
            "data": {
                "attributes": attrs,
                "id": params.filter_id,
                "type": "retention_filters",
            }
        }
        await api_request(
            f"rum/applications/{params.app_id}/retention_filters/{params.filter_id}", "v2",
            method="PATCH", json_body=body,
        )
        return f"Retention filter '{params.filter_id}' updated successfully."
    except Exception as exc:
        return handle_error(exc)


async def rum_retention_filter_delete(params: RumRetentionFilterDeleteInput) -> str:
    """Delete a retention filter for a RUM application."""
    try:
        await api_request(
            f"rum/applications/{params.app_id}/retention_filters/{params.filter_id}", "v2",
            method="DELETE",
        )
        return f"Retention filter '{params.filter_id}' deleted successfully."
    except Exception as exc:
        return handle_error(exc)


# ---------------------------------------------------------------------------
# Tool functions -- Sessions
# ---------------------------------------------------------------------------

def _sessions_body(
    from_time: str,
    to_time: Optional[str],
    limit: int,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the request body for RUM events search."""
    from_ts = parse_time(from_time)
    to_ts = parse_time(to_time) if to_time else now_unix()
    filt: Dict[str, Any] = {
        "from": str(from_ts * 1000),
        "to": str(to_ts * 1000),
    }
    if query:
        filt["query"] = query
    return {"filter": filt, "page": {"limit": limit}}


async def rum_sessions_list(params: RumSessionsListInput) -> str:
    """List recent RUM sessions/events within a time range."""
    try:
        body = _sessions_body(params.from_time, params.to_time, params.limit)
        data = await api_request(
            "rum/events/search", "v2", method="POST", json_body=body,
        )
        return format_output(data, params.response_format, _sessions_md)
    except Exception as exc:
        return handle_error(exc)


async def rum_sessions_search(params: RumSessionsSearchInput) -> str:
    """Search RUM sessions/events using query syntax."""
    try:
        body = _sessions_body(
            params.from_time, params.to_time, params.limit, params.query,
        )
        data = await api_request(
            "rum/events/search", "v2", method="POST", json_body=body,
        )
        return format_output(data, params.response_format, _sessions_md)
    except Exception as exc:
        return handle_error(exc)


# ---------------------------------------------------------------------------
# Tool functions -- Playlists
# ---------------------------------------------------------------------------

async def rum_playlists_list(params: RumPlaylistsListInput) -> str:
    """List session replay playlists."""
    try:
        data = await api_request("rum/playlists", "v2")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def rum_playlist_get(params: RumPlaylistGetInput) -> str:
    """Get a specific session replay playlist."""
    try:
        data = await api_request(f"rum/playlists/{params.playlist_id}", "v2")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


# ---------------------------------------------------------------------------
# Tool functions -- Heatmaps
# ---------------------------------------------------------------------------

async def rum_heatmap_query(params: RumHeatmapQueryInput) -> str:
    """Query heatmap data for a specific view/page."""
    try:
        from_ts = parse_time(params.from_time)
        to_ts = parse_time(params.to_time) if params.to_time else now_unix()
        qp: Dict[str, Any] = {
            "view": params.view,
            "from": from_ts,
            "to": to_ts,
        }
        data = await api_request("rum/analytics/heatmap", "v2", params=qp)
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)
