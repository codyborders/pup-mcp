"""Tests for Pydantic input model validation."""

import pytest
from pydantic import ValidationError

from pup_mcp.models.common import PaginatedInput, ResponseFormat
from pup_mcp.tools.monitors import MonitorGetInput, MonitorsListInput, MonitorsSearchInput


class TestPaginatedInput:
    def test_defaults(self) -> None:
        p = PaginatedInput()
        assert p.limit == 20
        assert p.offset == 0
        assert p.response_format == ResponseFormat.JSON

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PaginatedInput(limit=0)
        with pytest.raises(ValidationError):
            PaginatedInput(limit=101)

    def test_offset_non_negative(self) -> None:
        with pytest.raises(ValidationError):
            PaginatedInput(offset=-1)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            PaginatedInput(bogus="field")


class TestMonitorGetInput:
    def test_valid(self) -> None:
        m = MonitorGetInput(monitor_id=42)
        assert m.monitor_id == 42

    def test_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MonitorGetInput(monitor_id=0)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MonitorGetInput(monitor_id=-1)


class TestMonitorsSearchInput:
    def test_empty_query_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MonitorsSearchInput(query="")

    def test_per_page_bounds(self) -> None:
        with pytest.raises(ValidationError):
            MonitorsSearchInput(query="test", per_page=0)
        with pytest.raises(ValidationError):
            MonitorsSearchInput(query="test", per_page=101)


class TestMonitorsListInput:
    def test_optional_filters(self) -> None:
        m = MonitorsListInput()
        assert m.name is None
        assert m.tags is None

    def test_with_filters(self) -> None:
        m = MonitorsListInput(name="cpu", tags="env:prod")
        assert m.name == "cpu"
        assert m.tags == "env:prod"
