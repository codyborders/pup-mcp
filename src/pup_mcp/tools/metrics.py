"""Datadog metrics tools: query, search, list, and submit."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output
from pup_mcp.utils.time_parser import now_unix, parse_time_range


class MetricsQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, description="Metrics query (e.g. 'avg:system.cpu.user{*}')")
    from_time: str = Field(default="1h", alias="from", description="Start time: relative or absolute")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time (default: now)")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class MetricsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, description="Metric name search string")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class MetricsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filter_string: Optional[str] = Field(default=None, alias="filter", description="Filter metrics by name pattern")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class MetricSubmitInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric: str = Field(..., min_length=1, description="Metric name")
    value: float = Field(..., description="Metric value")
    metric_type: str = Field(default="gauge", description="Type: gauge, count, or rate")
    tags: Optional[List[str]] = Field(default=None, description="Tags list")
    host: Optional[str] = Field(default=None, description="Host name")


async def query_metrics(params: MetricsQueryInput) -> str:
    """Query Datadog time-series metrics with aggregation syntax."""
    try:
        from_ts, to_ts = parse_time_range(params.from_time, params.to_time)
        data = await api_request("query", "v1", params={"query": params.query, "from": from_ts, "to": to_ts})
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def search_metrics(params: MetricsSearchInput) -> str:
    """Search for metric names matching a query string."""
    try:
        data = await api_request("search", "v1", params={"q": f"metrics:{params.query}"})
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def list_metrics(params: MetricsListInput) -> str:
    """List available metrics, optionally filtered."""
    try:
        qp: Dict[str, Any] = {"from": now_unix() - 3600}
        if params.filter_string:
            qp["filter[tags]"] = params.filter_string
        data = await api_request("metrics", "v1", params=qp)
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def submit_metric(params: MetricSubmitInput) -> str:
    """Submit a custom metric data point to Datadog."""
    try:
        point: Dict[str, Any] = {
            "metric": params.metric,
            "type": params.metric_type,
            "points": [[now_unix(), params.value]],
        }
        if params.tags:
            point["tags"] = params.tags
        if params.host:
            point["host"] = params.host
        await api_request("series", "v1", method="POST", json_body={"series": [point]})
        return f"Metric '{params.metric}' submitted successfully (value={params.value})."
    except Exception as exc:
        return handle_error(exc)
