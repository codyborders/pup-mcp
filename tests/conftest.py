"""Shared pytest fixtures."""

import os

import pytest
import respx

from pup_mcp.models.settings import Settings


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure DD env vars are set for all tests."""
    monkeypatch.setenv("DD_API_KEY", "test-api-key")
    monkeypatch.setenv("DD_APP_KEY", "test-app-key")
    monkeypatch.setenv("DD_SITE", "datadoghq.com")


@pytest.fixture()
def settings() -> Settings:
    """Return a Settings instance with test credentials."""
    return Settings(
        dd_api_key="test-api-key",
        dd_app_key="test-app-key",
        dd_site="datadoghq.com",
    )


@pytest.fixture()
def mock_api() -> respx.MockRouter:
    """Provide a respx mock router scoped to each test.

    Usage::

        async def test_something(mock_api):
            mock_api.get("https://api.datadoghq.com/api/v1/monitor").respond(
                json=[{"id": 1, "name": "test"}]
            )
            ...
    """
    with respx.mock(assert_all_called=False) as router:
        yield router
