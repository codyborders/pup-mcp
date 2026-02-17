"""Tests for pup_mcp.tools.dashboards."""

import json

import pytest
import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.dashboards import (
    DashboardDeleteInput,
    DashboardGetInput,
    delete_dashboard,
    get_dashboard,
    list_dashboards,
)

BASE = "https://api.datadoghq.com/api/v1"


class TestListDashboards:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/dashboard").respond(
            json={"dashboards": [{"id": "abc-123", "title": "My Dash", "author_handle": "user@co.com"}]}
        )
        result = await list_dashboards(PaginatedInput())
        data = json.loads(result)
        assert len(data["dashboards"]) == 1

    @respx.mock
    async def test_returns_markdown(self) -> None:
        respx.get(f"{BASE}/dashboard").respond(
            json={"dashboards": [
                {"id": "abc-123", "title": "My Dash", "description": "Main dash", "author_handle": "user@co.com"}
            ]}
        )
        result = await list_dashboards(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "# Dashboards" in result
        assert "My Dash" in result
        assert "user@co.com" in result

    @respx.mock
    async def test_empty(self) -> None:
        respx.get(f"{BASE}/dashboard").respond(json={"dashboards": []})
        result = await list_dashboards(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "No dashboards found" in result


class TestGetDashboard:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/dashboard/abc-123").respond(
            json={"id": "abc-123", "title": "Test", "layout_type": "ordered",
                  "widgets": [{}], "description": "", "author_handle": "me",
                  "created_at": "2024-01-01", "modified_at": "2024-01-02"}
        )
        result = await get_dashboard(DashboardGetInput(dashboard_id="abc-123"))
        data = json.loads(result)
        assert data["id"] == "abc-123"

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE}/dashboard/abc-123").respond(
            json={"id": "abc-123", "title": "Test Dash", "layout_type": "ordered",
                  "widgets": [{}, {}], "description": "desc", "author_handle": "me",
                  "created_at": "2024-01-01", "modified_at": "2024-01-02"}
        )
        result = await get_dashboard(DashboardGetInput(
            dashboard_id="abc-123", response_format=ResponseFormat.MARKDOWN
        ))
        assert "# Dashboard: Test Dash" in result
        assert "**Widgets**: 2" in result


class TestDeleteDashboard:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/dashboard/abc-123").respond(status_code=204)
        result = await delete_dashboard(DashboardDeleteInput(dashboard_id="abc-123"))
        assert "deleted successfully" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE}/dashboard/nope").respond(status_code=404)
        result = await delete_dashboard(DashboardDeleteInput(dashboard_id="nope"))
        assert "not found" in result.lower()
