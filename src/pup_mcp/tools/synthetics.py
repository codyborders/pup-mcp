"""Datadog synthetic monitoring tools."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.services.datadog_client import api_request, handle_error
from pup_mcp.utils.formatting import format_output


class SyntheticsTestGetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    test_id: str = Field(..., min_length=1, description="Synthetic test public ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class SyntheticsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Optional[str] = Field(default=None, description="Search text")
    count: int = Field(default=50, ge=1, le=100, description="Number of results")
    start: int = Field(default=0, ge=0, description="Pagination offset")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


class SyntheticsCreateApiTestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, description="Test name")
    subtype: str = Field(
        default="http",
        description="API test subtype: http, ssl, dns, websocket, tcp, udp, icmp, or grpc",
    )
    config: Dict[str, Any] = Field(
        ...,
        description=(
            "Test config with 'assertions' list and 'request' object. "
            "Assertions have operator, target, and type. "
            "Request has method, url, headers, body, etc."
        ),
    )
    locations: List[str] = Field(
        ..., min_length=1, description="Locations to run from, e.g. ['aws:us-east-1']",
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Test options: tick_every, retry, follow_redirects, http_version, etc.",
    )
    message: Optional[str] = Field(default=None, description="Notification message")
    tags: Optional[List[str]] = Field(default=None, description="Tags list")
    status: Optional[str] = Field(default=None, description="Test status: 'live' or 'paused'")


class SyntheticsUpdateApiTestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    test_id: str = Field(..., min_length=1, description="Synthetic test public ID to update")
    name: str = Field(..., min_length=1, description="Test name")
    subtype: str = Field(
        default="http",
        description="API test subtype: http, ssl, dns, websocket, tcp, udp, icmp, or grpc",
    )
    config: Dict[str, Any] = Field(
        ...,
        description=(
            "Test config with 'assertions' list and 'request' object. "
            "Assertions have operator, target, and type. "
            "Request has method, url, headers, body, etc."
        ),
    )
    locations: List[str] = Field(
        ..., min_length=1, description="Locations to run from, e.g. ['aws:us-east-1']",
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Test options: tick_every, retry, follow_redirects, http_version, etc.",
    )
    message: Optional[str] = Field(default=None, description="Notification message")
    tags: Optional[List[str]] = Field(default=None, description="Tags list")
    status: Optional[str] = Field(default=None, description="Test status: 'live' or 'paused'")


class SyntheticsDeleteTestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_ids: List[str] = Field(
        ..., min_length=1, description="List of synthetic test public IDs to delete",
    )


def _tests_md(data: Any) -> str:
    tests: List[Dict[str, Any]] = data.get("tests", []) if isinstance(data, dict) else []
    if not tests:
        return "No synthetic tests found."
    lines = [f"# Synthetic Tests ({len(tests)})", ""]
    for t in tests:
        lines.append(f"## {t.get('name', '?')} ({t.get('public_id')})")
        lines.append(f"- **Type**: {t.get('type')}")
        lines.append(f"- **Status**: {t.get('status')}")
        lines.append("")
    return "\n".join(lines)


async def list_tests(params: PaginatedInput) -> str:
    """List all Datadog synthetic monitoring tests."""
    try:
        data = await api_request("synthetics/tests", "v1")
        return format_output(data, params.response_format, _tests_md)
    except Exception as exc:
        return handle_error(exc)


async def get_test(params: SyntheticsTestGetInput) -> str:
    """Get configuration for a specific synthetic test."""
    try:
        data = await api_request(f"synthetics/tests/{params.test_id}", "v1")
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def search_tests(params: SyntheticsSearchInput) -> str:
    """Search synthetic tests with optional text filter."""
    try:
        qp: Dict[str, Any] = {"count": params.count, "start": params.start}
        if params.text:
            qp["text"] = params.text
        data = await api_request("synthetics/tests/search", "v1", params=qp)
        return format_output(data, params.response_format)
    except Exception as exc:
        return handle_error(exc)


async def list_locations() -> str:
    """List available synthetic monitoring locations."""
    try:
        data = await api_request("synthetics/locations", "v1")
        return format_output(data, ResponseFormat.JSON)
    except Exception as exc:
        return handle_error(exc)


# ---------------------------------------------------------------------------
# Helper to build API test request body
# ---------------------------------------------------------------------------

def _api_test_body(
    name: str,
    subtype: str,
    config: Dict[str, Any],
    locations: List[str],
    options: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the JSON body for create/update API test requests."""
    body: Dict[str, Any] = {
        "name": name,
        "type": "api",
        "subtype": subtype,
        "config": config,
        "locations": locations,
    }
    if options is not None:
        body["options"] = options
    if message is not None:
        body["message"] = message
    if tags is not None:
        body["tags"] = tags
    if status is not None:
        body["status"] = status
    return body


# ---------------------------------------------------------------------------
# Create / Update / Delete API test tools
# ---------------------------------------------------------------------------

async def create_api_test(params: SyntheticsCreateApiTestInput) -> str:
    """Create a new Datadog Synthetics API test."""
    try:
        body = _api_test_body(
            name=params.name,
            subtype=params.subtype,
            config=params.config,
            locations=params.locations,
            options=params.options,
            message=params.message,
            tags=params.tags,
            status=params.status,
        )
        data = await api_request("synthetics/tests/api", "v1", method="POST", json_body=body)
        public_id = data.get("public_id", "unknown") if isinstance(data, dict) else "unknown"
        return f"Synthetic API test '{params.name}' created successfully (id={public_id})."
    except Exception as exc:
        return handle_error(exc)


async def update_api_test(params: SyntheticsUpdateApiTestInput) -> str:
    """Update an existing Datadog Synthetics API test."""
    try:
        body = _api_test_body(
            name=params.name,
            subtype=params.subtype,
            config=params.config,
            locations=params.locations,
            options=params.options,
            message=params.message,
            tags=params.tags,
            status=params.status,
        )
        await api_request(
            f"synthetics/tests/api/{params.test_id}", "v1", method="PUT", json_body=body,
        )
        return f"Synthetic API test {params.test_id} updated successfully."
    except Exception as exc:
        return handle_error(exc)


async def delete_test(params: SyntheticsDeleteTestInput) -> str:
    """Delete one or more Datadog Synthetics tests."""
    try:
        body = {"public_ids": params.public_ids}
        await api_request("synthetics/tests/delete", "v1", method="POST", json_body=body)
        count = len(params.public_ids)
        label = "test" if count == 1 else "tests"
        return f"{count} synthetic {label} deleted successfully."
    except Exception as exc:
        return handle_error(exc)
