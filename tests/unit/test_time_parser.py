"""Tests for pup_mcp.utils.time_parser."""

import time
from unittest.mock import patch

import pytest

from pup_mcp.exceptions import TimeParseError
from pup_mcp.utils.time_parser import now_unix, parse_time


class TestParseTimeRelative:
    """Test relative time format parsing."""

    @patch("pup_mcp.utils.time_parser.time.time", return_value=1700000000.0)
    def test_hours(self, mock_time: object) -> None:
        result = parse_time("1h")
        assert result == 1700000000 - 3600

    @patch("pup_mcp.utils.time_parser.time.time", return_value=1700000000.0)
    def test_minutes(self, mock_time: object) -> None:
        result = parse_time("30m")
        assert result == 1700000000 - 30 * 60

    @patch("pup_mcp.utils.time_parser.time.time", return_value=1700000000.0)
    def test_days(self, mock_time: object) -> None:
        result = parse_time("7d")
        assert result == 1700000000 - 7 * 86400

    @patch("pup_mcp.utils.time_parser.time.time", return_value=1700000000.0)
    def test_weeks(self, mock_time: object) -> None:
        result = parse_time("2w")
        assert result == 1700000000 - 2 * 604800

    @patch("pup_mcp.utils.time_parser.time.time", return_value=1700000000.0)
    def test_seconds(self, mock_time: object) -> None:
        result = parse_time("120s")
        assert result == 1700000000 - 120


class TestParseTimeAbsolute:
    """Test absolute time format parsing."""

    def test_unix_timestamp(self) -> None:
        assert parse_time("1700000000") == 1700000000

    def test_long_unix_timestamp(self) -> None:
        assert parse_time("17000000000") == 17000000000

    def test_iso8601_utc(self) -> None:
        result = parse_time("2024-01-15T10:30:00Z")
        assert isinstance(result, int)
        assert result > 0

    def test_iso8601_offset(self) -> None:
        result = parse_time("2024-01-15T10:30:00+00:00")
        assert isinstance(result, int)
        assert result > 0


class TestParseTimeInvalid:
    """Test error handling for invalid inputs."""

    def test_garbage_string(self) -> None:
        with pytest.raises(TimeParseError, match="Invalid time"):
            parse_time("not-a-time")

    def test_empty_string(self) -> None:
        with pytest.raises(TimeParseError, match="Invalid time"):
            parse_time("")

    def test_partial_relative(self) -> None:
        with pytest.raises(TimeParseError, match="Invalid time"):
            parse_time("1x")


class TestNowUnix:
    """Test now_unix helper."""

    def test_returns_int(self) -> None:
        result = now_unix()
        assert isinstance(result, int)
        assert abs(result - int(time.time())) <= 1
