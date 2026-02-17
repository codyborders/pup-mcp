"""Tests for pup_mcp.tools.synthetics."""

import json

import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.synthetics import (
    SyntheticsSearchInput,
    SyntheticsTestGetInput,
    get_test,
    list_locations,
    list_tests,
    search_tests,
)

BASE = "https://api.datadoghq.com/api/v1"


class TestListTests:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/synthetics/tests").respond(
            json={"tests": [{"public_id": "abc-123", "name": "Homepage", "type": "api", "status": "live"}]}
        )
        result = await list_tests(PaginatedInput())
        data = json.loads(result)
        assert len(data["tests"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE}/synthetics/tests").respond(
            json={"tests": [{"public_id": "abc-123", "name": "Homepage", "type": "api", "status": "live"}]}
        )
        result = await list_tests(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "# Synthetic Tests" in result
        assert "Homepage" in result

    @respx.mock
    async def test_empty_markdown(self) -> None:
        respx.get(f"{BASE}/synthetics/tests").respond(json={"tests": []})
        result = await list_tests(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "No synthetic tests found" in result


class TestGetTest:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/synthetics/tests/abc-123").respond(
            json={"public_id": "abc-123", "name": "Homepage"}
        )
        result = await get_test(SyntheticsTestGetInput(test_id="abc-123"))
        data = json.loads(result)
        assert data["public_id"] == "abc-123"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE}/synthetics/tests/bad").respond(status_code=404)
        result = await get_test(SyntheticsTestGetInput(test_id="bad"))
        assert "not found" in result.lower()


class TestSearchTests:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/synthetics/tests/search").respond(json={"tests": []})
        result = await search_tests(SyntheticsSearchInput())
        data = json.loads(result)
        assert "tests" in data

    @respx.mock
    async def test_with_text(self) -> None:
        route = respx.get(f"{BASE}/synthetics/tests/search").respond(json={"tests": []})
        await search_tests(SyntheticsSearchInput(text="homepage"))
        assert route.calls[0].request.url.params["text"] == "homepage"

    @respx.mock
    async def test_without_text(self) -> None:
        route = respx.get(f"{BASE}/synthetics/tests/search").respond(json={"tests": []})
        await search_tests(SyntheticsSearchInput())
        assert "text" not in dict(route.calls[0].request.url.params)


class TestListLocations:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/synthetics/locations").respond(
            json={"locations": [{"id": "aws:us-east-1", "name": "US East"}]}
        )
        result = await list_locations()
        data = json.loads(result)
        assert len(data["locations"]) == 1
