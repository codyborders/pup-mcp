"""Tests for pup_mcp.tools.slos."""

import json

import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.slos import SloDeleteInput, SloGetInput, delete_slo, get_slo, list_slos

BASE = "https://api.datadoghq.com/api/v1"


class TestListSlos:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/slo").respond(
            json={"data": [{"id": "slo1", "name": "Uptime", "type": "metric",
                            "description": "99.9% uptime", "thresholds": [{"target": 99.9, "timeframe": "30d"}]}]}
        )
        result = await list_slos(PaginatedInput())
        data = json.loads(result)
        assert len(data["data"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE}/slo").respond(
            json={"data": [{"id": "slo1", "name": "Uptime", "type": "metric",
                            "description": "99.9% uptime", "thresholds": [{"target": 99.9, "timeframe": "30d"}]}]}
        )
        result = await list_slos(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "# SLOs" in result
        assert "99.9%" in result

    @respx.mock
    async def test_empty(self) -> None:
        respx.get(f"{BASE}/slo").respond(json={"data": []})
        result = await list_slos(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "No SLOs found" in result


class TestGetSlo:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/slo/slo1").respond(json={"data": {"id": "slo1", "name": "Uptime"}})
        result = await get_slo(SloGetInput(slo_id="slo1"))
        data = json.loads(result)
        assert data["data"]["id"] == "slo1"


class TestDeleteSlo:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/slo/slo1").respond(status_code=204)
        result = await delete_slo(SloDeleteInput(slo_id="slo1"))
        assert "deleted successfully" in result
