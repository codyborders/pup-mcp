"""Tests for pup_mcp.services.datadog_client."""

import httpx
import pytest

from pup_mcp.exceptions import ConfigurationError, DatadogApiError
from pup_mcp.services.datadog_client import handle_error


class TestHandleError:
    """Test error message formatting."""

    def test_datadog_api_404(self) -> None:
        exc = DatadogApiError("not found", status_code=404, body="")
        result = handle_error(exc)
        assert "Resource not found" in result

    def test_datadog_api_401(self) -> None:
        exc = DatadogApiError("unauth", status_code=401, body="")
        result = handle_error(exc)
        assert "Unauthorized" in result

    def test_datadog_api_403(self) -> None:
        exc = DatadogApiError("forbidden", status_code=403, body="")
        result = handle_error(exc)
        assert "Forbidden" in result

    def test_datadog_api_429(self) -> None:
        exc = DatadogApiError("rate limited", status_code=429, body="")
        result = handle_error(exc)
        assert "Rate limit" in result

    def test_datadog_api_500_with_json_body(self) -> None:
        exc = DatadogApiError("server error", status_code=500, body='{"errors": ["boom"]}')
        result = handle_error(exc)
        assert "500" in result
        assert "boom" in result

    def test_datadog_api_500_with_text_body(self) -> None:
        exc = DatadogApiError("server error", status_code=500, body="Internal Server Error")
        result = handle_error(exc)
        assert "Internal Server Error" in result

    def test_configuration_error(self) -> None:
        exc = ConfigurationError("missing keys")
        result = handle_error(exc)
        assert "missing keys" in result

    def test_timeout_exception(self) -> None:
        exc = httpx.ReadTimeout("timed out")
        result = handle_error(exc)
        assert "timed out" in result.lower()

    def test_connect_error(self) -> None:
        exc = httpx.ConnectError("connection refused")
        result = handle_error(exc)
        assert "Could not reach" in result

    def test_unexpected_error(self) -> None:
        exc = RuntimeError("surprise")
        result = handle_error(exc)
        assert "RuntimeError" in result
        assert "surprise" in result
