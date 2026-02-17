"""Tests for pup_mcp.tools.incidents."""

import json

import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.incidents import IncidentGetInput, get_incident, list_incidents

BASE_V2 = "https://api.datadoghq.com/api/v2"


class TestListIncidents:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V2}/incidents").respond(
            json={"data": [{"id": "inc1", "attributes": {"title": "Outage", "state": "active", "severity": "SEV-1", "created": "2024-01-01"}}]}
        )
        result = await list_incidents(PaginatedInput())
        data = json.loads(result)
        assert len(data["data"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE_V2}/incidents").respond(
            json={"data": [{"id": "inc1", "attributes": {"title": "Outage", "state": "active", "severity": "SEV-1", "created": "2024-01-01"}}]}
        )
        result = await list_incidents(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "# Incidents" in result
        assert "Outage" in result

    @respx.mock
    async def test_empty(self) -> None:
        respx.get(f"{BASE_V2}/incidents").respond(json={"data": []})
        result = await list_incidents(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "No incidents found" in result

    @respx.mock
    async def test_pagination_params(self) -> None:
        route = respx.get(f"{BASE_V2}/incidents").respond(json={"data": []})
        await list_incidents(PaginatedInput(limit=5, offset=10))
        params = route.calls[0].request.url.params
        assert params["page[size]"] == "5"
        assert params["page[offset]"] == "10"


class TestGetIncident:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V2}/incidents/inc1").respond(
            json={"data": {"id": "inc1", "attributes": {"title": "Outage"}}}
        )
        result = await get_incident(IncidentGetInput(incident_id="inc1"))
        data = json.loads(result)
        assert data["data"]["id"] == "inc1"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE_V2}/incidents/bad").respond(status_code=404)
        result = await get_incident(IncidentGetInput(incident_id="bad"))
        assert "not found" in result.lower()
