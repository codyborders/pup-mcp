"""Async HTTP client for the Datadog API."""

import json
import logging
from typing import Any, Dict, Optional

import httpx

from pup_mcp.exceptions import ConfigurationError, DatadogApiError
from pup_mcp.models.settings import Settings, get_settings

logger = logging.getLogger(__name__)

API_TIMEOUT = 30.0


def _base_url(settings: Settings, version: str = "v1") -> str:
    return f"https://api.{settings.dd_site}/api/{version}"


def _auth_headers(settings: Settings) -> Dict[str, str]:
    return {
        "DD-API-KEY": settings.dd_api_key,
        "DD-APPLICATION-KEY": settings.dd_app_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def api_request(
    endpoint: str,
    version: str = "v1",
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    settings: Optional[Settings] = None,
) -> Any:
    """Make an authenticated request to the Datadog API.

    Args:
        endpoint: API path after ``/api/{version}/``.
        version: API version, ``"v1"`` or ``"v2"``.
        method: HTTP method.
        params: Query parameters.
        json_body: JSON request body.
        settings: Optional settings override (useful for testing).

    Returns:
        Parsed JSON response, or ``None`` for 204 responses.

    Raises:
        ConfigurationError: If API credentials are not configured.
        DatadogApiError: If the API returns a non-2xx status.
        httpx.TimeoutException: On request timeout.
        httpx.ConnectError: On network failure.
    """
    try:
        cfg = settings or get_settings()
    except Exception as exc:
        raise ConfigurationError(
            "DD_API_KEY and DD_APP_KEY must be set in environment or .env file."
        ) from exc

    url = f"{_base_url(cfg, version)}/{endpoint}"
    logger.debug("Datadog API %s %s", method, url)

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.request(
            method,
            url,
            headers=_auth_headers(cfg),
            params=params,
            json=json_body,
        )

    if response.status_code >= 400:
        raise DatadogApiError(
            f"Datadog API returned {response.status_code}",
            status_code=response.status_code,
            body=response.text,
        )

    if response.status_code == 204:
        return None
    return response.json()


def handle_error(exc: Exception) -> str:
    """Convert an exception into an actionable error message string.

    Args:
        exc: The caught exception.

    Returns:
        A human-readable error string suitable for returning from a tool.
    """
    if isinstance(exc, DatadogApiError):
        status = exc.status_code
        messages: Dict[int, str] = {
            400: "Bad request. Check your parameters.",
            401: "Unauthorized. Check that DD_API_KEY and DD_APP_KEY are valid.",
            403: "Forbidden. Your API key lacks permission for this operation.",
            404: "Resource not found. Check the ID is correct.",
            429: "Rate limit exceeded. Wait before retrying.",
        }
        msg = messages.get(status, f"Datadog API returned status {status}.")
        body_str = ""
        if exc.body:
            try:
                parsed = json.loads(exc.body)
                body_str = f"\n{json.dumps(parsed, indent=2)}"
            except (json.JSONDecodeError, TypeError):
                body_str = f"\n{exc.body}"
        return f"Error: {msg}{body_str}"

    if isinstance(exc, ConfigurationError):
        return f"Error: {exc}"

    if isinstance(exc, httpx.TimeoutException):
        return "Error: Request timed out. Try again."

    if isinstance(exc, httpx.ConnectError):
        return "Error: Could not reach Datadog API. Check DD_SITE and network."

    logger.error("Unexpected error in tool", exc_info=exc)
    return f"Error: {type(exc).__name__}: {exc}"
