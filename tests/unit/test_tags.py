"""Tests for pup_mcp.tools.tags."""

import json

import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.tags import (
    TagsDeleteInput,
    TagsGetInput,
    TagsModifyInput,
    add_tags,
    delete_tags,
    get_tags,
    list_tags,
    update_tags,
)

BASE = "https://api.datadoghq.com/api/v1"


class TestListTags:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE}/tags/hosts").respond(json={"tags": {"env:prod": ["host1"]}})
        result = await list_tags(PaginatedInput())
        data = json.loads(result)
        assert "tags" in data


class TestGetTags:
    @respx.mock
    async def test_returns_tags(self) -> None:
        respx.get(f"{BASE}/tags/hosts/myhost").respond(json={"tags": ["env:prod", "role:web"]})
        result = await get_tags(TagsGetInput(host="myhost"))
        data = json.loads(result)
        assert "env:prod" in data["tags"]


class TestAddTags:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.post(f"{BASE}/tags/hosts/myhost").respond(
            json={"host": "myhost", "tags": ["env:prod"]}
        )
        result = await add_tags(TagsModifyInput(host="myhost", tags=["env:prod"]))
        data = json.loads(result)
        assert data["tags"] == ["env:prod"]
        body = json.loads(route.calls[0].request.content)
        assert body["tags"] == ["env:prod"]


class TestUpdateTags:
    @respx.mock
    async def test_success(self) -> None:
        route = respx.put(f"{BASE}/tags/hosts/myhost").respond(
            json={"host": "myhost", "tags": ["env:staging"]}
        )
        result = await update_tags(TagsModifyInput(host="myhost", tags=["env:staging"]))
        data = json.loads(result)
        assert data["tags"] == ["env:staging"]


class TestDeleteTags:
    @respx.mock
    async def test_success(self) -> None:
        respx.delete(f"{BASE}/tags/hosts/myhost").respond(status_code=204)
        result = await delete_tags(TagsDeleteInput(host="myhost"))
        assert "deleted" in result.lower()

    @respx.mock
    async def test_not_found(self) -> None:
        respx.delete(f"{BASE}/tags/hosts/nope").respond(status_code=404)
        result = await delete_tags(TagsDeleteInput(host="nope"))
        assert "not found" in result.lower()
