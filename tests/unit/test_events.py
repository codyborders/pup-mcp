"""Tests for pup_mcp.tools.events."""

import json

import respx

from pup_mcp.tools.events import (
    EventGetInput,
    EventsListInput,
    EventsSearchInput,
    get_event,
    list_events,
    search_events,
)

BASE_V1 = "https://api.datadoghq.com/api/v1"
BASE_V2 = "https://api.datadoghq.com/api/v2"


class TestListEvents:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V1}/events").respond(
            json={"events": [{"id": "evt1", "title": "Deploy"}]}
        )
        result = await list_events(EventsListInput())
        data = json.loads(result)
        assert "events" in data

    @respx.mock
    async def test_with_tags(self) -> None:
        route = respx.get(f"{BASE_V1}/events").respond(json={"events": []})
        await list_events(EventsListInput(tags="env:prod"))
        assert route.calls[0].request.url.params["tags"] == "env:prod"


class TestSearchEvents:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.post(f"{BASE_V2}/events/search").respond(
            json={"data": [{"id": "evt1"}]}
        )
        result = await search_events(EventsSearchInput(query="source:deploy"))
        data = json.loads(result)
        assert "data" in data

    @respx.mock
    async def test_passes_body(self) -> None:
        route = respx.post(f"{BASE_V2}/events/search").respond(json={"data": []})
        await search_events(EventsSearchInput(query="source:deploy", limit=5))
        body = json.loads(route.calls[0].request.content)
        assert body["filter"]["query"] == "source:deploy"
        assert body["page"]["limit"] == 5


class TestGetEvent:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V1}/events/evt1").respond(
            json={"event": {"id": "evt1", "title": "Deploy"}}
        )
        result = await get_event(EventGetInput(event_id="evt1"))
        data = json.loads(result)
        assert data["event"]["id"] == "evt1"

    @respx.mock
    async def test_api_error(self) -> None:
        respx.get(f"{BASE_V1}/events/bad").respond(status_code=404)
        result = await get_event(EventGetInput(event_id="bad"))
        assert "not found" in result.lower()
