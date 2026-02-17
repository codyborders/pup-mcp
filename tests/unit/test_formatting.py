"""Tests for pup_mcp.utils.formatting."""

import json

from pup_mcp.models.common import ResponseFormat
from pup_mcp.utils.formatting import CHARACTER_LIMIT, format_output


class TestFormatOutput:
    """Test format_output with JSON and Markdown modes."""

    def test_json_format(self) -> None:
        data = {"key": "value", "count": 42}
        result = format_output(data, ResponseFormat.JSON)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["count"] == 42

    def test_markdown_format_with_renderer(self) -> None:
        data = [{"name": "test"}]
        renderer = lambda d: f"# Items ({len(d)})"
        result = format_output(data, ResponseFormat.MARKDOWN, renderer)
        assert result == "# Items (1)"

    def test_markdown_format_without_renderer_falls_back_to_json(self) -> None:
        data = {"key": "value"}
        result = format_output(data, ResponseFormat.MARKDOWN)
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_truncation(self) -> None:
        data = "x" * (CHARACTER_LIMIT + 1000)
        result = format_output(data, ResponseFormat.JSON)
        assert len(result) < CHARACTER_LIMIT + 200
        assert "[Truncated" in result

    def test_no_truncation_under_limit(self) -> None:
        data = {"short": "data"}
        result = format_output(data, ResponseFormat.JSON)
        assert "[Truncated" not in result
