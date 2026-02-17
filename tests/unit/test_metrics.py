"""Tests for pup_mcp.tools.metrics."""

import json

import respx

from pup_mcp.tools.metrics import (
    MetricSubmitInput,
    MetricsListInput,
    MetricsQueryInput,
    MetricsSearchInput,
    list_metrics,
    query_metrics,
    search_metrics,
    submit_metric,
)

BASE = "https://api.datadoghq.com/api/v1"


class TestQueryMetrics:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/query").respond(
            json={"series": [{"metric": "system.cpu.user", "pointlist": [[1, 42.0]]}]}
        )
        result = await query_metrics(MetricsQueryInput(query="avg:system.cpu.user{*}"))
        data = json.loads(result)
        assert "series" in data

    @respx.mock
    async def test_passes_params(self) -> None:
        route = respx.get(f"{BASE}/query").respond(json={"series": []})
        await query_metrics(MetricsQueryInput(query="avg:system.cpu.user{*}"))
        params = route.calls[0].request.url.params
        assert params["query"] == "avg:system.cpu.user{*}"
        assert "from" in params
        assert "to" in params

    @respx.mock
    async def test_api_error(self) -> None:
        respx.get(f"{BASE}/query").respond(status_code=400)
        result = await query_metrics(MetricsQueryInput(query="bad"))
        assert "Error" in result


class TestSearchMetrics:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/search").respond(
            json={"results": {"metrics": ["system.cpu.user", "system.cpu.system"]}}
        )
        result = await search_metrics(MetricsSearchInput(query="system.cpu"))
        data = json.loads(result)
        assert "results" in data

    @respx.mock
    async def test_passes_query(self) -> None:
        route = respx.get(f"{BASE}/search").respond(json={"results": {"metrics": []}})
        await search_metrics(MetricsSearchInput(query="disk"))
        assert route.calls[0].request.url.params["q"] == "metrics:disk"


class TestListMetrics:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/metrics").respond(json={"metrics": ["system.cpu.user"]})
        result = await list_metrics(MetricsListInput())
        data = json.loads(result)
        assert "metrics" in data

    @respx.mock
    async def test_with_filter(self) -> None:
        route = respx.get(f"{BASE}/metrics").respond(json={"metrics": []})
        await list_metrics(MetricsListInput(**{"filter": "env:prod"}))
        assert "filter[tags]" in dict(route.calls[0].request.url.params)


class TestSubmitMetric:
    @respx.mock
    async def test_success(self) -> None:
        respx.post(f"{BASE}/series").respond(json={"status": "ok"})
        result = await submit_metric(MetricSubmitInput(metric="custom.metric", value=42.0))
        assert "submitted successfully" in result
        assert "custom.metric" in result

    @respx.mock
    async def test_with_tags_and_host(self) -> None:
        route = respx.post(f"{BASE}/series").respond(json={"status": "ok"})
        await submit_metric(
            MetricSubmitInput(metric="custom.metric", value=1.5, tags=["env:prod"], host="web01")
        )
        body = json.loads(route.calls[0].request.content)
        assert body["series"][0]["tags"] == ["env:prod"]
        assert body["series"][0]["host"] == "web01"

    @respx.mock
    async def test_api_error(self) -> None:
        respx.post(f"{BASE}/series").respond(status_code=403)
        result = await submit_metric(MetricSubmitInput(metric="x", value=0))
        assert "Error" in result
