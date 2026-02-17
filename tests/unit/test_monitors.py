"""Tests for pup_mcp.tools.monitors."""

import json

import httpx
import pytest
import respx

from pup_mcp.models.common import ResponseFormat
from pup_mcp.tools.monitors import (
    MonitorDeleteInput,
    MonitorGetInput,
    MonitorsListInput,
    MonitorsSearchInput,
    delete_monitor,
    get_monitor,
    list_monitors,
    search_monitors,
)

BASE = "https://api.datadoghq.com/api/v1"


class TestListMonitors:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/monitor").respond(
            json=[{"id": 1, "name": "CPU Alert", "type": "metric", "overall_state": "OK", "tags": []}]
        )
        result = await list_monitors(MonitorsListInput())
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["name"] == "CPU Alert"

    @respx.mock
    async def test_returns_markdown(self) -> None:
        respx.get(f"{BASE}/monitor").respond(
            json=[{"id": 1, "name": "CPU Alert", "type": "metric", "overall_state": "OK", "tags": ["env:prod"]}]
        )
        result = await list_monitors(MonitorsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "# Monitors" in result
        assert "CPU Alert" in result
        assert "env:prod" in result

    @respx.mock
    async def test_empty_list(self) -> None:
        respx.get(f"{BASE}/monitor").respond(json=[])
        result = await list_monitors(MonitorsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "No monitors found" in result

    @respx.mock
    async def test_with_name_filter(self) -> None:
        route = respx.get(f"{BASE}/monitor").respond(json=[])
        await list_monitors(MonitorsListInput(name="cpu"))
        assert route.calls[0].request.url.params["name"] == "cpu"

    @respx.mock
    async def test_with_tags_filter(self) -> None:
        route = respx.get(f"{BASE}/monitor").respond(json=[])
        await list_monitors(MonitorsListInput(tags="env:prod"))
        assert route.calls[0].request.url.params["monitor_tags"] == "env:prod"

    @respx.mock
    async def test_api_error(self) -> None:
        respx.get(f"{BASE}/monitor").respond(status_code=403)
        result = await list_monitors(MonitorsListInput())
        assert "Error" in result


class TestGetMonitor:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/monitor/123").respond(
            json={"id": 123, "name": "Disk Alert", "type": "metric", "overall_state": "Alert",
                  "query": "avg:system.disk{*}", "message": "Disk full", "created": "2024-01-01",
                  "modified": "2024-01-02", "tags": []}
        )
        result = await get_monitor(MonitorGetInput(monitor_id=123))
        data = json.loads(result)
        assert data["id"] == 123

    @respx.mock
    async def test_returns_markdown(self) -> None:
        respx.get(f"{BASE}/monitor/123").respond(
            json={"id": 123, "name": "Disk Alert", "type": "metric", "overall_state": "Alert",
                  "query": "avg:system.disk{*}", "message": "Disk full", "created": "2024-01-01",
                  "modified": "2024-01-02", "tags": ["team:infra"]}
        )
        result = await get_monitor(MonitorGetInput(monitor_id=123, response_format=ResponseFormat.MARKDOWN))
        assert "# Monitor: Disk Alert" in result
        assert "team:infra" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE}/monitor/999").respond(status_code=404)
        result = await get_monitor(MonitorGetInput(monitor_id=999))
        assert "not found" in result.lower()


class TestSearchMonitors:
    @respx.mock
    async def test_basic_search(self) -> None:
        respx.get(f"{BASE}/monitor/search").respond(
            json={"monitors": [], "metadata": {"total_count": 0}}
        )
        result = await search_monitors(MonitorsSearchInput(query="type:metric"))
        data = json.loads(result)
        assert "monitors" in data

    @respx.mock
    async def test_passes_params(self) -> None:
        route = respx.get(f"{BASE}/monitor/search").respond(json={"monitors": []})
        await search_monitors(MonitorsSearchInput(query="status:alert", page=2, per_page=10, sort="name,asc"))
        params = route.calls[0].request.url.params
        assert params["query"] == "status:alert"
        assert params["page"] == "2"
        assert params["per_page"] == "10"
        assert params["sort"] == "name,asc"


class TestDeleteMonitor:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/monitor/123").respond(status_code=204)
        result = await delete_monitor(MonitorDeleteInput(monitor_id=123))
        assert "deleted successfully" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE}/monitor/999").respond(status_code=404)
        result = await delete_monitor(MonitorDeleteInput(monitor_id=999))
        assert "not found" in result.lower()
