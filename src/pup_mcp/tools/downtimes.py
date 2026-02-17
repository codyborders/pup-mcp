"""Datadog downtime management tools."""

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


class DowntimeGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    downtime_id: str = Field(..., min_length=1, description="Downtime ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class DowntimeCancelInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    downtime_id: str = Field(..., min_length=1, description="Downtime ID to cancel")


async def list_downtimes(params: PaginatedInput) -> str:
    """List all scheduled downtimes."""
    try:
        data = await api_request("downtime", "v2")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def get_downtime(params: DowntimeGetInput) -> str:
    """Get details for a specific downtime."""
    try:
        data = await api_request(f"downtime/{params.downtime_id}", "v2")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def cancel_downtime(params: DowntimeCancelInput) -> str:
    """Cancel a scheduled downtime."""
    try:
        await api_request(f"downtime/{params.downtime_id}", "v2", method="DELETE")
        return f"Downtime {params.downtime_id} cancelled successfully."
    except Exception as exc:
        return handle_error(exc)
