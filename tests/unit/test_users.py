"""Tests for pup_mcp.tools.users."""

import json

import respx

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.users import UserGetInput, get_user, list_roles, list_users

BASE_V1 = "https://api.datadoghq.com/api/v1"
BASE_V2 = "https://api.datadoghq.com/api/v2"


class TestListUsers:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V1}/user").respond(
            json={"users": [{"handle": "user@co.com", "name": "Test User", "email": "user@co.com", "role": "admin", "disabled": False}]}
        )
        result = await list_users(PaginatedInput())
        data = json.loads(result)
        assert len(data["users"]) == 1

    @respx.mock
    async def test_markdown(self) -> None:
        respx.get(f"{BASE_V1}/user").respond(
            json={"users": [{"handle": "user@co.com", "name": "Test User", "email": "user@co.com", "role": "admin", "disabled": False}]}
        )
        result = await list_users(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "# Users" in result
        assert "Test User" in result

    @respx.mock
    async def test_empty_markdown(self) -> None:
        respx.get(f"{BASE_V1}/user").respond(json={"users": []})
        result = await list_users(PaginatedInput(response_format=ResponseFormat.MARKDOWN))
        assert "No users found" in result


class TestGetUser:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V1}/user/user123").respond(
            json={"user": {"handle": "user@co.com", "name": "Test"}}
        )
        result = await get_user(UserGetInput(user_id="user123"))
        data = json.loads(result)
        assert data["user"]["handle"] == "user@co.com"

    @respx.mock
    async def test_not_found(self) -> None:
        respx.get(f"{BASE_V1}/user/bad").respond(status_code=404)
        result = await get_user(UserGetInput(user_id="bad"))
        assert "not found" in result.lower()


class TestListRoles:
    @respx.mock
    async def test_returns_json(self) -> None:
        respx.get(f"{BASE_V2}/roles").respond(
            json={"data": [{"id": "role1", "attributes": {"name": "Admin"}}]}
        )
        result = await list_roles()
        data = json.loads(result)
        assert len(data["data"]) == 1
