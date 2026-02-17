"""Tests for pup_mcp.tools.downtimes."""

import json

import respx

from pup_mcp.models.common import PaginatedInput
from pup_mcp.tools.downtimes import (
    DowntimeCancelInput,
    DowntimeGetInput,
    cancel_downtime,
    get_downtime,
    list_downtimes,
)

BASE_V2 = "https://api.datadoghq.com/api/v2"


class TestListDowntimes:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V2}/downtime").respond(
            json={"data": [{"id": "dt1", "type": "downtime"}]}
        )
        result = await list_downtimes(PaginatedInput())
        data = json.loads(result)
        assert "data" in data

    @respx.mock
    async def test_api_error(self) -> None:
        respx.get(f"{BASE_V2}/downtime").respond(status_code=403)
        result = await list_downtimes(PaginatedInput())
        assert "Error" in result


class TestGetDowntime:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V2}/downtime/dt1").respond(
            json={"data": {"id": "dt1", "type": "downtime"}}
        )
        result = await get_downtime(DowntimeGetInput(downtime_id="dt1"))
        data = json.loads(result)
        assert data["data"]["id"] == "dt1"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE_V2}/downtime/bad").respond(status_code=404)
        result = await get_downtime(DowntimeGetInput(downtime_id="bad"))
        assert "not found" in result.lower()


class TestCancelDowntime:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE_V2}/downtime/dt1").respond(status_code=204)
        result = await cancel_downtime(DowntimeCancelInput(downtime_id="dt1"))
        assert "cancelled successfully" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE_V2}/downtime/bad").respond(status_code=404)
        result = await cancel_downtime(DowntimeCancelInput(downtime_id="bad"))
        assert "not found" in result.lower()
