"""Tests for pup_mcp.exceptions."""

from pup_mcp.exceptions import (
    ConfigurationError,
    DatadogApiError,
    PupMcpError,
    TimeParseError,
)


class TestExceptionHierarchy:
    """Verify exception inheritance."""

    def test_configuration_error_is_pup_mcp_error(self) -> None:
        assert issubclass(ConfigurationError, PupMcpError)

    def test_datadog_api_error_is_pup_mcp_error(self) -> None:
        assert issubclass(DatadogApiError, PupMcpError)

    def test_time_parse_error_is_pup_mcp_error(self) -> None:
        assert issubclass(TimeParseError, PupMcpError)


class TestDatadogApiError:
    """Test DatadogApiError attributes."""

    def test_attributes(self) -> None:
        err = DatadogApiError("not found", status_code=404, body='{"errors": ["nope"]}')
        assert err.status_code == 404
        assert err.body == '{"errors": ["nope"]}'
        assert "not found" in str(err)
