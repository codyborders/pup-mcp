"""Response formatting and truncation utilities."""

import json
from typing import Any, Callable, Optional

from pup_mcp.models.common import ResponseFormat

CHARACTER_LIMIT = 25_000


def format_output(
    data: Any,
    fmt: ResponseFormat,
    markdown_renderer: Optional[Callable[[Any], str]] = None,
) -> str:
    """Format API response data as JSON or Markdown.

    Args:
        data: The raw data from the Datadog API.
        fmt: Desired output format.
        markdown_renderer: Optional callable that converts *data* to a
            Markdown string.  Used only when *fmt* is MARKDOWN.

    Returns:
        A string representation of the data, truncated if it exceeds
        CHARACTER_LIMIT.
    """
    if fmt == ResponseFormat.MARKDOWN and markdown_renderer is not None:
        return _truncate(markdown_renderer(data))
    return _truncate(json.dumps(data, indent=2, default=str))


def _truncate(text: str) -> str:
    """Truncate text that exceeds CHARACTER_LIMIT."""
    if len(text) <= CHARACTER_LIMIT:
        return text
    return (
        text[:CHARACTER_LIMIT]
        + "\n\n[Truncated. Use pagination or filters to narrow results.]"
    )
