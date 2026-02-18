"""Tests for pup_mcp.tools.synthetics."""

import json

import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.synthetics import (
    SyntheticsCreateApiTestInput,
    SyntheticsDeleteTestInput,
    SyntheticsSearchInput,
    SyntheticsTestGetInput,
    SyntheticsUpdateApiTestInput,
    create_api_test,
    delete_test,
    get_test,
    list_locations,
    list_tests,
    search_tests,
    update_api_test,
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


# ---------------------------------------------------------------------------
# Create API test
# ---------------------------------------------------------------------------

_MINIMAL_CONFIG: dict = {
    "assertions": [
        {"operator": "is", "target": 200, "type": "statusCode"},
    ],
    "request": {"method": "GET", "url": "https://example.com"},
}


class TestCreateApiTest:
    @respx.mock
    async def test_creates_http_test(self) -> None:
        route = respx.post(f"{BASE}/synthetics/tests/api").respond(
            json={
                "public_id": "abc-def-ghi",
                "name": "My HTTP Test",
                "type": "api",
                "subtype": "http",
            }
        )
        result = await create_api_test(
            SyntheticsCreateApiTestInput(
                name="My HTTP Test",
                subtype="http",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1"],
            )
        )
        assert "created successfully" in result
        assert "abc-def-ghi" in result
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "My HTTP Test"
        assert body["type"] == "api"
        assert body["subtype"] == "http"
        assert body["config"] == _MINIMAL_CONFIG
        assert body["locations"] == ["aws:us-east-1"]

    @respx.mock
    async def test_creates_ssl_test(self) -> None:
        ssl_config: dict = {
            "assertions": [
                {"operator": "isInMoreThan", "target": 30, "type": "certificate"},
            ],
            "request": {"host": "example.com", "port": 443},
        }
        route = respx.post(f"{BASE}/synthetics/tests/api").respond(
            json={"public_id": "ssl-123", "name": "SSL Check", "type": "api", "subtype": "ssl"}
        )
        result = await create_api_test(
            SyntheticsCreateApiTestInput(
                name="SSL Check",
                subtype="ssl",
                config=ssl_config,
                locations=["aws:eu-west-1"],
            )
        )
        assert "created successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["subtype"] == "ssl"

    @respx.mock
    async def test_with_all_optional_fields(self) -> None:
        route = respx.post(f"{BASE}/synthetics/tests/api").respond(
            json={"public_id": "full-123", "name": "Full Test"}
        )
        result = await create_api_test(
            SyntheticsCreateApiTestInput(
                name="Full Test",
                subtype="http",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1", "aws:eu-west-1"],
                options={
                    "tick_every": 60,
                    "min_failure_duration": 10,
                    "min_location_failed": 1,
                    "retry": {"count": 3, "interval": 10},
                    "follow_redirects": True,
                    "http_version": "http2",
                },
                message="Alert: test failing!",
                tags=["env:staging", "team:backend"],
                status="live",
            )
        )
        assert "created successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["message"] == "Alert: test failing!"
        assert body["tags"] == ["env:staging", "team:backend"]
        assert body["status"] == "live"
        assert body["options"]["tick_every"] == 60
        assert body["options"]["retry"]["count"] == 3
        assert body["locations"] == ["aws:us-east-1", "aws:eu-west-1"]

    @respx.mock
    async def test_without_optional_fields(self) -> None:
        route = respx.post(f"{BASE}/synthetics/tests/api").respond(
            json={"public_id": "min-123"}
        )
        await create_api_test(
            SyntheticsCreateApiTestInput(
                name="Minimal",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1"],
            )
        )
        body = json.loads(route.calls[0].request.content)
        assert "message" not in body
        assert "tags" not in body
        assert "status" not in body
        assert "options" not in body
        # subtype defaults to "http"
        assert body["subtype"] == "http"

    @respx.mock
    async def test_api_error(self) -> None:
        respx.post(f"{BASE}/synthetics/tests/api").respond(status_code=400)
        result = await create_api_test(
            SyntheticsCreateApiTestInput(
                name="Bad",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1"],
            )
        )
        assert "Error" in result

    @respx.mock
    async def test_config_with_multiple_assertions(self) -> None:
        multi_config: dict = {
            "assertions": [
                {"operator": "is", "target": 200, "type": "statusCode"},
                {"operator": "lessThan", "target": 2000, "type": "responseTime"},
                {"operator": "contains", "target": "OK", "type": "body"},
            ],
            "request": {
                "method": "POST",
                "url": "https://api.example.com/health",
                "headers": {"Content-Type": "application/json"},
                "body": '{"check": true}',
            },
        }
        route = respx.post(f"{BASE}/synthetics/tests/api").respond(
            json={"public_id": "multi-123"}
        )
        await create_api_test(
            SyntheticsCreateApiTestInput(
                name="Multi-Assert",
                config=multi_config,
                locations=["aws:us-east-1"],
            )
        )
        body = json.loads(route.calls[0].request.content)
        assert len(body["config"]["assertions"]) == 3
        assert body["config"]["request"]["method"] == "POST"
        assert body["config"]["request"]["headers"]["Content-Type"] == "application/json"


# ---------------------------------------------------------------------------
# Update API test
# ---------------------------------------------------------------------------


class TestUpdateApiTest:
    @respx.mock
    async def test_updates_test(self) -> None:
        route = respx.put(f"{BASE}/synthetics/tests/api/abc-123").respond(
            json={"public_id": "abc-123", "name": "Updated Test"}
        )
        result = await update_api_test(
            SyntheticsUpdateApiTestInput(
                test_id="abc-123",
                name="Updated Test",
                subtype="http",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1"],
            )
        )
        assert "updated successfully" in result
        assert "abc-123" in result
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "Updated Test"
        assert body["type"] == "api"
        assert body["subtype"] == "http"

    @respx.mock
    async def test_update_with_options(self) -> None:
        route = respx.put(f"{BASE}/synthetics/tests/api/xyz-789").respond(
            json={"public_id": "xyz-789", "name": "Opt Test"}
        )
        await update_api_test(
            SyntheticsUpdateApiTestInput(
                test_id="xyz-789",
                name="Opt Test",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-west-2"],
                options={"tick_every": 300, "follow_redirects": False},
                message="Updated alert",
                tags=["env:prod"],
                status="paused",
            )
        )
        body = json.loads(route.calls[0].request.content)
        assert body["options"]["tick_every"] == 300
        assert body["message"] == "Updated alert"
        assert body["tags"] == ["env:prod"]
        assert body["status"] == "paused"

    @respx.mock
    async def test_update_without_optional_fields(self) -> None:
        route = respx.put(f"{BASE}/synthetics/tests/api/abc-123").respond(
            json={"public_id": "abc-123"}
        )
        await update_api_test(
            SyntheticsUpdateApiTestInput(
                test_id="abc-123",
                name="Minimal Update",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1"],
            )
        )
        body = json.loads(route.calls[0].request.content)
        assert "message" not in body
        assert "tags" not in body
        assert "status" not in body
        assert "options" not in body

    @respx.mock
    async def test_not_found(self) -> None:
        respx.put(f"{BASE}/synthetics/tests/api/bad").respond(status_code=404)
        result = await update_api_test(
            SyntheticsUpdateApiTestInput(
                test_id="bad",
                name="X",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1"],
            )
        )
        assert "not found" in result.lower()

    @respx.mock
    async def test_api_error(self) -> None:
        respx.put(f"{BASE}/synthetics/tests/api/abc-123").respond(status_code=400)
        result = await update_api_test(
            SyntheticsUpdateApiTestInput(
                test_id="abc-123",
                name="Bad",
                config=_MINIMAL_CONFIG,
                locations=["aws:us-east-1"],
            )
        )
        assert "Error" in result


# ---------------------------------------------------------------------------
# Delete test(s)
# ---------------------------------------------------------------------------


class TestDeleteTest:
    @respx.mock
    async def test_delete_single(self) -> None:
        route = respx.post(f"{BASE}/synthetics/tests/delete").respond(
            json={"deleted_tests": [{"public_id": "abc-123", "deleted_at": "2024-01-01T00:00:00Z"}]}
        )
        result = await delete_test(SyntheticsDeleteTestInput(public_ids=["abc-123"]))
        assert "deleted successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["public_ids"] == ["abc-123"]

    @respx.mock
    async def test_delete_multiple(self) -> None:
        route = respx.post(f"{BASE}/synthetics/tests/delete").respond(
            json={
                "deleted_tests": [
                    {"public_id": "abc-123"},
                    {"public_id": "def-456"},
                ]
            }
        )
        result = await delete_test(
            SyntheticsDeleteTestInput(public_ids=["abc-123", "def-456"])
        )
        assert "deleted successfully" in result
        assert "2" in result
        body = json.loads(route.calls[0].request.content)
        assert len(body["public_ids"]) == 2

    @respx.mock
    async def test_not_found(self) -> None:
        respx.post(f"{BASE}/synthetics/tests/delete").respond(status_code=404)
        result = await delete_test(SyntheticsDeleteTestInput(public_ids=["bad-id"]))
        assert "not found" in result.lower()

    @respx.mock
    async def test_api_error(self) -> None:
        respx.post(f"{BASE}/synthetics/tests/delete").respond(status_code=403)
        result = await delete_test(SyntheticsDeleteTestInput(public_ids=["abc-123"]))
        assert "Error" in result
