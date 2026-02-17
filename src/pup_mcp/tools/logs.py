"""Datadog log search tools."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output
from pup_mcp.utils.time_parser import now_unix, parse_time


class LogsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(default="*", description="Log search query")
    from_time: str = Field(default="1h", alias="from", description="Start time")
    to_time: Optional[str] = Field(default=None, alias="to", description="End time")
    limit: int = Field(default=20, ge=1, le=1000, description="Max entries")
    sort: str = Field(default="desc", description="Sort order: 'asc' or 'desc'")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


def _logs_md(data: Any) -> str:
    logs: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    if not logs:
        return "No log entries found."
    lines = [f"# Logs ({len(logs)} entries)", ""]
    for entry in logs:
        attrs = entry.get("attributes", {})
        lines.append(
            f"**[{attrs.get('timestamp', '?')}]** "
            f"`{attrs.get('status', '?')}` "
            f"{attrs.get('service', '?')}"
        )
        lines.append(f"  {attrs.get('message', '(no message)')}")
        lines.append("")
    return "\n".join(lines)


async def search_logs(params: LogsSearchInput) -> str:
    """Search Datadog logs using query syntax with time range and pagination."""
    try:
        from_ts = parse_time(params.from_time)
        to_ts = parse_time(params.to_time) if params.to_time else now_unix()
        body = {
            "filter": {
                "query": params.query,
                "from": str(from_ts * 1000),
                "to": str(to_ts * 1000),
            },
            "sort": "timestamp" if params.sort == "asc" else "-timestamp",
            "page": {"limit": params.limit},
        }
        data = await api_request("logs/events/search", "v2", method="POST", json_body=body)
        return format_output(data, params.response_format, _logs_md)
    except Exception as exc:
        return handle_error(exc)
