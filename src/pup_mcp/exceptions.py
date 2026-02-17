"""Domain-specific exception hierarchy for the pup MCP server."""


class PupMcpError(Exception):
    """Base exception for all pup MCP errors."""


class ConfigurationError(PupMcpError):
    """Raised when required configuration is missing or invalid."""


class DatadogApiError(PupMcpError):
    """Raised when a Datadog API call fails.

    Attributes:
        status_code: HTTP status code from the API response.
        body: Response body text or parsed dict.
    """

    def __init__(self, message: str, status_code: int, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class TimeParseError(PupMcpError):
    """Raised when a time string cannot be parsed."""
