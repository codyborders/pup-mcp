"""Tests for pup_mcp.models.settings."""

import pytest

from pup_mcp.models.settings import Settings


class TestSettings:
    """Test Settings Pydantic model."""

    def test_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DD_API_KEY", "abc")
        monkeypatch.setenv("DD_APP_KEY", "def")
        s = Settings()
        assert s.dd_api_key == "abc"
        assert s.dd_app_key == "def"
        assert s.dd_site == "datadoghq.com"

    def test_custom_site(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DD_API_KEY", "abc")
        monkeypatch.setenv("DD_APP_KEY", "def")
        monkeypatch.setenv("DD_SITE", "datadoghq.eu")
        s = Settings()
        assert s.dd_site == "datadoghq.eu"

    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DD_API_KEY", raising=False)
        monkeypatch.setenv("DD_APP_KEY", "def")
        with pytest.raises(Exception):
            Settings(_env_file=None)

    def test_missing_app_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DD_API_KEY", "abc")
        monkeypatch.delenv("DD_APP_KEY", raising=False)
        with pytest.raises(Exception):
            Settings(_env_file=None)
