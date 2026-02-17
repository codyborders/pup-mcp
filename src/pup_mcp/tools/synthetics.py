"""Datadog synthetic monitoring tools."""

import json
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
        return json.dumps(data, indent=2, default=str)
    except Exception as exc:
        return handle_error(exc)
