"""Datadog event tools: list, search, get."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output
from pup_mcp.utils.time_parser import parse_time_range


class EventsListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_time: str = Field(default="1h", alias="from", description="Start time")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class EventsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(default="*", description="Event search query")
    from_time: str = Field(default="1h", alias="from", description="Start time")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class EventGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(..., min_length=1, description="Event ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


async def list_events(params: EventsListInput) -> str:
    """List recent Datadog events within a time range."""
    try:
        from_ts, to_ts = parse_time_range(params.from_time, params.to_time)
        qp: Dict[str, Any] = {"start": from_ts, "end": to_ts}
        if params.tags:
            qp["tags"] = params.tags
        data = await api_request("events", "v1", params=qp)
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def search_events(params: EventsSearchInput) -> str:
    """Search Datadog events using query syntax."""
    try:
        from_ts, to_ts = parse_time_range(params.from_time, params.to_time)
        body = {
            "filter": {"query": params.query, "from": str(from_ts), "to": str(to_ts)},
            "page": {"limit": params.limit},
        }
        data = await api_request("events/search", "v2", method="POST", json_body=body)
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def get_event(params: EventGetInput) -> str:
    """Get details for a specific Datadog event by ID."""
    try:
        data = await api_request(f"events/{params.event_id}", "v1")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)
