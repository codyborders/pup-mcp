"""Tests for pup_mcp.tools.logs."""

import json

import respx

from pup_mcp.models.common import ResponseFormat
from pup_mcp.tools.logs import LogsSearchInput, search_logs

BASE_V2 = "https://api.datadoghq.com/api/v2"


class TestSearchLogs:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.post(f"{BASE_V2}/logs/events/search").respond(
            json={"data": [{"id": "log1", "attributes": {"message": "hello", "timestamp": "2024-01-01", "status": "info", "service": "web"}}]}
        )
        result = await search_logs(LogsSearchInput())
        data = json.loads(result)
        assert "data" in data

    @respx.mock
    async def test_markdown(self) -> None:
        respx.post(f"{BASE_V2}/logs/events/search").respond(
            json={"data": [{"id": "log1", "attributes": {"message": "hello", "timestamp": "2024-01-01", "status": "info", "service": "web"}}]}
        )
        result = await search_logs(LogsSearchInput(response_format=ResponseFormat.MARKDOWN))
        assert "# Logs" in result
        assert "hello" in result

    @respx.mock
    async def test_empty_markdown(self) -> None:
        respx.post(f"{BASE_V2}/logs/events/search").respond(json={"data": []})
        result = await search_logs(LogsSearchInput(response_format=ResponseFormat.MARKDOWN))
        assert "No log entries found" in result

    @respx.mock
    async def test_passes_body(self) -> None:
        route = respx.post(f"{BASE_V2}/logs/events/search").respond(json={"data": []})
        await search_logs(LogsSearchInput(query="service:web", limit=10, sort="asc"))
        body = json.loads(route.calls[0].request.content)
        assert body["filter"]["query"] == "service:web"
        assert body["page"]["limit"] == 10
        assert body["sort"] == "timestamp"

    @respx.mock
    async def test_sort_desc(self) -> None:
        route = respx.post(f"{BASE_V2}/logs/events/search").respond(json={"data": []})
        await search_logs(LogsSearchInput(sort="desc"))
        body = json.loads(route.calls[0].request.content)
        assert body["sort"] == "-timestamp"

    @respx.mock
    async def test_api_error(self) -> None:
        respx.post(f"{BASE_V2}/logs/events/search").respond(status_code=403)
        result = await search_logs(LogsSearchInput())
        assert "Error" in result
