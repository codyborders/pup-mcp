"""Tests for pup_mcp.tools.slos."""

import json

import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.slos import (
    SloCorrectionsInput,
    SloCreateInput,
    SloDeleteInput,
    SloGetInput,
    SloUpdateInput,
    create_slo,
    delete_slo,
    get_slo,
    get_slo_corrections,
    list_slos,
    update_slo,
)

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

    @respx.mock
    async def test_api_error(self) -> None:
        respx.get(f"{BASE}/slo").respond(status_code=403)
        result = await list_slos(PaginatedInput())
        assert "Error" in result


class TestGetSlo:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/slo/slo1").respond(json={"data": {"id": "slo1", "name": "Uptime"}})
        result = await get_slo(SloGetInput(slo_id="slo1"))
        data = json.loads(result)
        assert data["data"]["id"] == "slo1"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE}/slo/bad").respond(status_code=404)
        result = await get_slo(SloGetInput(slo_id="bad"))
        assert "not found" in result.lower()


class TestCreateSlo:
    @respx.mock
    async def test_metric_slo(self) -> None:
        route = respx.post(f"{BASE}/slo").respond(
            json={"data": [{"id": "new-slo", "name": "API Availability"}]}
        )
        result = await create_slo(SloCreateInput(
            name="API Availability",
            slo_type="metric",
            thresholds=[{"target": 99.9, "timeframe": "30d"}],
            query={"numerator": "sum:requests{status:2xx}", "denominator": "sum:requests"},
        ))
        assert "created successfully" in result
        assert "new-slo" in result
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "API Availability"
        assert body["type"] == "metric"
        assert body["thresholds"][0]["target"] == 99.9
        assert body["query"]["numerator"] == "sum:requests{status:2xx}"

    @respx.mock
    async def test_monitor_slo(self) -> None:
        route = respx.post(f"{BASE}/slo").respond(
            json={"data": [{"id": "mon-slo", "name": "Monitor Uptime"}]}
        )
        result = await create_slo(SloCreateInput(
            name="Monitor Uptime",
            slo_type="monitor",
            thresholds=[{"target": 99.5, "timeframe": "7d"}],
            monitor_ids=[123, 456],
        ))
        assert "created successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["type"] == "monitor"
        assert body["monitor_ids"] == [123, 456]

    @respx.mock
    async def test_with_optional_fields(self) -> None:
        route = respx.post(f"{BASE}/slo").respond(
            json={"data": [{"id": "s1", "name": "Test"}]}
        )
        await create_slo(SloCreateInput(
            name="Test",
            slo_type="metric",
            thresholds=[{"target": 99.0, "timeframe": "30d"}],
            description="My test SLO",
            tags=["team:backend", "env:prod"],
            query={"numerator": "sum:ok{*}", "denominator": "sum:total{*}"},
        ))
        body = json.loads(route.calls[0].request.content)
        assert body["description"] == "My test SLO"
        assert body["tags"] == ["team:backend", "env:prod"]

    @respx.mock
    async def test_without_optional_fields(self) -> None:
        route = respx.post(f"{BASE}/slo").respond(
            json={"data": [{"id": "s1"}]}
        )
        await create_slo(SloCreateInput(
            name="Minimal",
            slo_type="metric",
            thresholds=[{"target": 99.0, "timeframe": "30d"}],
        ))
        body = json.loads(route.calls[0].request.content)
        assert "description" not in body
        assert "tags" not in body
        assert "monitor_ids" not in body
        assert "query" not in body

    @respx.mock
    async def test_api_error(self) -> None:
        respx.post(f"{BASE}/slo").respond(status_code=400)
        result = await create_slo(SloCreateInput(
            name="Bad", slo_type="metric",
            thresholds=[{"target": 99.0, "timeframe": "30d"}],
        ))
        assert "Error" in result


class TestUpdateSlo:
    @respx.mock
    async def test_update_name_and_description(self) -> None:
        route = respx.put(f"{BASE}/slo/slo1").respond(
            json={"data": [{"id": "slo1", "name": "Updated"}]}
        )
        result = await update_slo(SloUpdateInput(
            slo_id="slo1",
            name="Updated",
            slo_type="metric",
            thresholds=[{"target": 99.9, "timeframe": "30d"}],
            description="Updated desc",
        ))
        assert "updated successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "Updated"
        assert body["description"] == "Updated desc"
        assert body["type"] == "metric"

    @respx.mock
    async def test_update_thresholds(self) -> None:
        route = respx.put(f"{BASE}/slo/slo1").respond(
            json={"data": [{"id": "slo1"}]}
        )
        await update_slo(SloUpdateInput(
            slo_id="slo1",
            name="Same",
            slo_type="metric",
            thresholds=[{"target": 99.99, "timeframe": "30d", "warning": 99.95}],
        ))
        body = json.loads(route.calls[0].request.content)
        assert body["thresholds"][0]["target"] == 99.99
        assert body["thresholds"][0]["warning"] == 99.95

    @respx.mock
    async def test_not_found(self) -> None:
        respx.put(f"{BASE}/slo/bad").respond(status_code=404)
        result = await update_slo(SloUpdateInput(
            slo_id="bad", name="X", slo_type="metric",
            thresholds=[{"target": 99.0, "timeframe": "30d"}],
        ))
        assert "not found" in result.lower()


class TestGetSloCorrections:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/slo/slo1/corrections").respond(
            json={"data": [{"id": "corr1", "attributes": {
                "category": "scheduled_maintenance",
                "description": "Planned downtime",
                "start": 1700000000, "end": 1700003600,
            }}]}
        )
        result = await get_slo_corrections(SloCorrectionsInput(slo_id="slo1"))
        data = json.loads(result)
        assert len(data["data"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE}/slo/slo1/corrections").respond(
            json={"data": [{"id": "corr1", "attributes": {
                "category": "scheduled_maintenance",
                "description": "Planned downtime",
                "start": 1700000000, "end": 1700003600,
            }}]}
        )
        result = await get_slo_corrections(
            SloCorrectionsInput(slo_id="slo1", response_format=ResponseFormat.MARKDOWN)
        )
        assert "# SLO Corrections" in result
        assert "Planned downtime" in result
        assert "scheduled_maintenance" in result

    @respx.mock
    async def test_empty_markdown(self) -> None:
        respx.get(f"{BASE}/slo/slo1/corrections").respond(json={"data": []})
        result = await get_slo_corrections(
            SloCorrectionsInput(slo_id="slo1", response_format=ResponseFormat.MARKDOWN)
        )
        assert "No corrections found" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE}/slo/bad/corrections").respond(status_code=404)
        result = await get_slo_corrections(SloCorrectionsInput(slo_id="bad"))
        assert "not found" in result.lower()


class TestDeleteSlo:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/slo/slo1").respond(status_code=204)
        result = await delete_slo(SloDeleteInput(slo_id="slo1"))
        assert "deleted successfully" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE}/slo/bad").respond(status_code=404)
        result = await delete_slo(SloDeleteInput(slo_id="bad"))
        assert "not found" in result.lower()
