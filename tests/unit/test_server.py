"""Tests for pup_mcp.server -- verifies tool registration."""

from pup_mcp.server import mcp


class TestServerRegistration:
    def test_mcp_instance_exists(self) -> None:
        assert mcp.name == "pup_mcp"

    def test_all_tools_registered(self) -> None:
        tool_names = {t.name for t in mcp._tool_manager.list_tools()}
        expected = {
            "pup_monitors_list", "pup_monitors_get", "pup_monitors_search", "pup_monitors_delete",
            "pup_dashboards_list", "pup_dashboards_get", "pup_dashboards_delete",
            "pup_metrics_query", "pup_metrics_search", "pup_metrics_list", "pup_metrics_submit",
            "pup_logs_search",
            "pup_events_list", "pup_events_search", "pup_events_get",
            "pup_incidents_list", "pup_incidents_get",
            "pup_slos_list", "pup_slos_get", "pup_slos_delete",
            "pup_synthetics_tests_list", "pup_synthetics_tests_get",
            "pup_synthetics_tests_search", "pup_synthetics_locations_list",
            "pup_downtimes_list", "pup_downtimes_get", "pup_downtimes_cancel",
            "pup_tags_list", "pup_tags_get", "pup_tags_add", "pup_tags_update", "pup_tags_delete",
            "pup_users_list", "pup_users_get", "pup_roles_list",
        }
        assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"

    def test_tool_count(self) -> None:
        tools = mcp._tool_manager.list_tools()
        assert len(tools) == 35
