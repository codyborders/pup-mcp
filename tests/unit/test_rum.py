"""Tests for pup_mcp.tools.rum."""

import json

import respx

from pup_mcp.models.common import ResponseFormat
from pup_mcp.tools.rum import (
    RumAppCreateInput,
    RumAppDeleteInput,
    RumAppGetInput,
    RumAppUpdateInput,
    RumAppsListInput,
    RumHeatmapQueryInput,
    RumMetricCreateInput,
    RumMetricDeleteInput,
    RumMetricGetInput,
    RumMetricUpdateInput,
    RumMetricsListInput,
    RumPlaylistGetInput,
    RumPlaylistsListInput,
    RumRetentionFilterCreateInput,
    RumRetentionFilterDeleteInput,
    RumRetentionFilterGetInput,
    RumRetentionFilterUpdateInput,
    RumRetentionFiltersListInput,
    RumSessionsListInput,
    RumSessionsSearchInput,
    rum_app_create,
    rum_app_delete,
    rum_app_get,
    rum_app_update,
    rum_apps_list,
    rum_heatmap_query,
    rum_metric_create,
    rum_metric_delete,
    rum_metric_get,
    rum_metric_update,
    rum_metrics_list,
    rum_playlist_get,
    rum_playlists_list,
    rum_retention_filter_create,
    rum_retention_filter_delete,
    rum_retention_filter_get,
    rum_retention_filter_update,
    rum_retention_filters_list,
    rum_sessions_list,
    rum_sessions_search,
)

BASE = "https://api.datadoghq.com/api/v2"


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------


class TestRumAppsList:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/applications").respond(
            json={"data": [{"id": "app1", "attributes": {"name": "MyApp", "type": "browser", "created_at": "2024-01-01"}}]}
        )
        result = await rum_apps_list(RumAppsListInput())
        data = json.loads(result)
        assert len(data["data"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE}/rum/applications").respond(
            json={"data": [{"id": "app1", "attributes": {"name": "MyApp", "type": "browser", "created_at": "2024-01-01"}}]}
        )
        result = await rum_apps_list(RumAppsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "# RUM Applications" in result
        assert "MyApp" in result

    @respx.mock
    async def test_empty_markdown(self) -> None:
        respx.get(f"{BASE}/rum/applications").respond(json={"data": []})
        result = await rum_apps_list(RumAppsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "No RUM applications found" in result


class TestRumAppGet:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/applications/app1").respond(
            json={"data": {"id": "app1", "attributes": {"name": "MyApp"}}}
        )
        result = await rum_app_get(RumAppGetInput(app_id="app1"))
        data = json.loads(result)
        assert data["data"]["id"] == "app1"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE}/rum/applications/bad").respond(status_code=404)
        result = await rum_app_get(RumAppGetInput(app_id="bad"))
        assert "not found" in result.lower()


class TestRumAppCreate:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.post(f"{BASE}/rum/applications").respond(
            json={"data": {"id": "new-app", "attributes": {"name": "Web"}}}
        )
        result = await rum_app_create(RumAppCreateInput(name="Web", **{"type": "browser"}))
        assert "created successfully" in result
        assert "new-app" in result
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"]["name"] == "Web"
        assert body["data"]["attributes"]["type"] == "browser"

    @respx.mock
    async def test_api_error(self) -> None:
        respx.post(f"{BASE}/rum/applications").respond(status_code=400)
        result = await rum_app_create(RumAppCreateInput(name="Bad", **{"type": "browser"}))
        assert "Error" in result


class TestRumAppUpdate:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.patch(f"{BASE}/rum/applications/app1").respond(
            json={"data": {"id": "app1", "attributes": {"name": "Updated"}}}
        )
        result = await rum_app_update(RumAppUpdateInput(app_id="app1", name="Updated"))
        data = json.loads(result)
        assert data["data"]["attributes"]["name"] == "Updated"
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"]["name"] == "Updated"

    @respx.mock
    async def test_no_changes(self) -> None:
        route = respx.patch(f"{BASE}/rum/applications/app1").respond(
            json={"data": {"id": "app1"}}
        )
        await rum_app_update(RumAppUpdateInput(app_id="app1"))
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"] == {}


class TestRumAppDelete:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/rum/applications/app1").respond(status_code=204)
        result = await rum_app_delete(RumAppDeleteInput(app_id="app1"))
        assert "deleted successfully" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE}/rum/applications/bad").respond(status_code=404)
        result = await rum_app_delete(RumAppDeleteInput(app_id="bad"))
        assert "not found" in result.lower()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestRumMetricsList:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/metrics").respond(
            json={"data": [{"id": "m1", "attributes": {"path": "rum.view.count", "event_type": "views", "compute": {"aggregation_type": "count"}}}]}
        )
        result = await rum_metrics_list(RumMetricsListInput())
        data = json.loads(result)
        assert len(data["data"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE}/rum/metrics").respond(
            json={"data": [{"id": "m1", "attributes": {"path": "rum.view.count", "event_type": "views", "compute": {"aggregation_type": "count"}}}]}
        )
        result = await rum_metrics_list(RumMetricsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "# RUM Metrics" in result
        assert "rum.view.count" in result

    @respx.mock
    async def test_empty_markdown(self) -> None:
        respx.get(f"{BASE}/rum/metrics").respond(json={"data": []})
        result = await rum_metrics_list(RumMetricsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "No RUM metrics found" in result


class TestRumMetricGet:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/metrics/m1").respond(
            json={"data": {"id": "m1", "attributes": {"path": "rum.view.count"}}}
        )
        result = await rum_metric_get(RumMetricGetInput(metric_id="m1"))
        data = json.loads(result)
        assert data["data"]["id"] == "m1"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE}/rum/metrics/bad").respond(status_code=404)
        result = await rum_metric_get(RumMetricGetInput(metric_id="bad"))
        assert "not found" in result.lower()


class TestRumMetricCreate:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.post(f"{BASE}/rum/metrics").respond(json={"data": {"id": "new_metric"}})
        result = await rum_metric_create(
            RumMetricCreateInput(name="rum.custom", event_type="views")
        )
        assert "created successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["id"] == "rum.custom"
        assert body["data"]["attributes"]["event_type"] == "views"

    @respx.mock
    async def test_with_filter_and_group_by(self) -> None:
        route = respx.post(f"{BASE}/rum/metrics").respond(json={"data": {"id": "m"}})
        await rum_metric_create(
            RumMetricCreateInput(
                name="rum.custom", event_type="views",
                group_by=["@view.name"], **{"filter": "@type:view"},
            )
        )
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"]["filter"]["query"] == "@type:view"
        assert body["data"]["attributes"]["group_by"][0]["path"] == "@view.name"


class TestRumMetricUpdate:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.patch(f"{BASE}/rum/metrics/m1").respond(json={"data": {"id": "m1"}})
        result = await rum_metric_update(
            RumMetricUpdateInput(metric_id="m1", compute_type="distribution")
        )
        assert "updated successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"]["compute"]["aggregation_type"] == "distribution"


class TestRumMetricDelete:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/rum/metrics/m1").respond(status_code=204)
        result = await rum_metric_delete(RumMetricDeleteInput(metric_id="m1"))
        assert "deleted successfully" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE}/rum/metrics/bad").respond(status_code=404)
        result = await rum_metric_delete(RumMetricDeleteInput(metric_id="bad"))
        assert "not found" in result.lower()


# ---------------------------------------------------------------------------
# Retention Filters
# ---------------------------------------------------------------------------


class TestRumRetentionFiltersList:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/applications/app1/retention_filters").respond(
            json={"data": [{"id": "rf1", "attributes": {"name": "Keep All"}}]}
        )
        result = await rum_retention_filters_list(
            RumRetentionFiltersListInput(app_id="app1")
        )
        data = json.loads(result)
        assert len(data["data"]) == 1


class TestRumRetentionFilterGet:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/applications/app1/retention_filters/rf1").respond(
            json={"data": {"id": "rf1", "attributes": {"name": "Keep All"}}}
        )
        result = await rum_retention_filter_get(
            RumRetentionFilterGetInput(app_id="app1", filter_id="rf1")
        )
        data = json.loads(result)
        assert data["data"]["id"] == "rf1"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE}/rum/applications/app1/retention_filters/bad").respond(status_code=404)
        result = await rum_retention_filter_get(
            RumRetentionFilterGetInput(app_id="app1", filter_id="bad")
        )
        assert "not found" in result.lower()


class TestRumRetentionFilterCreate:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.post(f"{BASE}/rum/applications/app1/retention_filters").respond(
            json={"data": {"id": "rf_new"}}
        )
        result = await rum_retention_filter_create(
            RumRetentionFilterCreateInput(app_id="app1", name="My Filter", query="@type:view", rate=50)
        )
        assert "created successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"]["name"] == "My Filter"
        assert body["data"]["attributes"]["sample_rate"] == 50


class TestRumRetentionFilterUpdate:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.patch(f"{BASE}/rum/applications/app1/retention_filters/rf1").respond(
            json={"data": {"id": "rf1"}}
        )
        result = await rum_retention_filter_update(
            RumRetentionFilterUpdateInput(app_id="app1", filter_id="rf1", rate=75)
        )
        assert "updated successfully" in result
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"]["sample_rate"] == 75

    @respx.mock
    async def test_partial_update(self) -> None:
        route = respx.patch(f"{BASE}/rum/applications/app1/retention_filters/rf1").respond(
            json={"data": {"id": "rf1"}}
        )
        await rum_retention_filter_update(
            RumRetentionFilterUpdateInput(app_id="app1", filter_id="rf1", enabled=False)
        )
        body = json.loads(route.calls[0].request.content)
        assert body["data"]["attributes"]["enabled"] is False
        assert "sample_rate" not in body["data"]["attributes"]


class TestRumRetentionFilterDelete:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/rum/applications/app1/retention_filters/rf1").respond(status_code=204)
        result = await rum_retention_filter_delete(
            RumRetentionFilterDeleteInput(app_id="app1", filter_id="rf1")
        )
        assert "deleted successfully" in result

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE}/rum/applications/app1/retention_filters/bad").respond(status_code=404)
        result = await rum_retention_filter_delete(
            RumRetentionFilterDeleteInput(app_id="app1", filter_id="bad")
        )
        assert "not found" in result.lower()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class TestRumSessionsList:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.post(f"{BASE}/rum/events/search").respond(
            json={"data": [{"id": "s1", "attributes": {"timestamp": "2024-01-01", "service": "web", "type": "view", "session": {"id": "sess1"}}}]}
        )
        result = await rum_sessions_list(RumSessionsListInput())
        data = json.loads(result)
        assert len(data["data"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.post(f"{BASE}/rum/events/search").respond(
            json={"data": [{"id": "s1", "attributes": {"timestamp": "2024-01-01", "service": "web", "type": "view", "session": {"id": "sess1"}}}]}
        )
        result = await rum_sessions_list(RumSessionsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "# RUM Sessions" in result
        assert "sess1" in result

    @respx.mock
    async def test_empty_markdown(self) -> None:
        respx.post(f"{BASE}/rum/events/search").respond(json={"data": []})
        result = await rum_sessions_list(RumSessionsListInput(response_format=ResponseFormat.MARKDOWN))
        assert "No RUM sessions found" in result

    @respx.mock
    async def test_passes_time_and_limit(self) -> None:
        route = respx.post(f"{BASE}/rum/events/search").respond(json={"data": []})
        await rum_sessions_list(RumSessionsListInput(limit=50))
        body = json.loads(route.calls[0].request.content)
        assert body["page"]["limit"] == 50
        assert "from" in body["filter"]
        assert "to" in body["filter"]


class TestRumSessionsSearch:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.post(f"{BASE}/rum/events/search").respond(
            json={"data": [{"id": "s1"}]}
        )
        result = await rum_sessions_search(RumSessionsSearchInput(query="@type:view"))
        data = json.loads(result)
        assert "data" in data

    @respx.mock
    async def test_passes_query(self) -> None:
        route = respx.post(f"{BASE}/rum/events/search").respond(json={"data": []})
        await rum_sessions_search(RumSessionsSearchInput(query="@type:error", limit=10))
        body = json.loads(route.calls[0].request.content)
        assert body["filter"]["query"] == "@type:error"
        assert body["page"]["limit"] == 10

    @respx.mock
    async def test_api_error(self) -> None:
        respx.post(f"{BASE}/rum/events/search").respond(status_code=403)
        result = await rum_sessions_search(RumSessionsSearchInput(query="@type:view"))
        assert "Error" in result


# ---------------------------------------------------------------------------
# Playlists
# ---------------------------------------------------------------------------


class TestRumPlaylistsList:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/playlists").respond(
            json={"data": [{"id": "pl1", "attributes": {"name": "My Playlist"}}]}
        )
        result = await rum_playlists_list(RumPlaylistsListInput())
        data = json.loads(result)
        assert len(data["data"]) == 1

    @respx.mock
    async def test_api_error(self) -> None:
        respx.get(f"{BASE}/rum/playlists").respond(status_code=404)
        result = await rum_playlists_list(RumPlaylistsListInput())
        assert "not found" in result.lower()


class TestRumPlaylistGet:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/playlists/pl1").respond(
            json={"data": {"id": "pl1", "attributes": {"name": "My Playlist"}}}
        )
        result = await rum_playlist_get(RumPlaylistGetInput(playlist_id="pl1"))
        data = json.loads(result)
        assert data["data"]["id"] == "pl1"


# ---------------------------------------------------------------------------
# Heatmaps
# ---------------------------------------------------------------------------


class TestRumHeatmapQuery:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/rum/analytics/heatmap").respond(
            json={"data": {"clicks": [{"x": 100, "y": 200, "count": 42}]}}
        )
        result = await rum_heatmap_query(RumHeatmapQueryInput(view="/home"))
        data = json.loads(result)
        assert "data" in data

    @respx.mock
    async def test_passes_params(self) -> None:
        route = respx.get(f"{BASE}/rum/analytics/heatmap").respond(json={"data": {}})
        await rum_heatmap_query(RumHeatmapQueryInput(view="/checkout"))
        params = route.calls[0].request.url.params
        assert params["view"] == "/checkout"
        assert "from" in params
        assert "to" in params

    @respx.mock
    async def test_api_error(self) -> None:
        respx.get(f"{BASE}/rum/analytics/heatmap").respond(status_code=400)
        result = await rum_heatmap_query(RumHeatmapQueryInput(view="/bad"))
        assert "Error" in result
