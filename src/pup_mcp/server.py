"""MCP server entry point -- registers all tools and starts the server."""

import logging
from typing import Any, Callable, Dict

from mcp.server.fastmcp import FastMCP

from pup_mcp.tools import (
    dashboards,
    downtimes,
    events,
    incidents,
    logs,
    metrics,
    monitors,
    rum,
    slos,
    synthetics,
    tags,
    users,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP("pup_mcp")

# -- Annotation presets for MCP tool hints ----------------------------------

_READ_ONLY: Dict[str, Any] = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

_WRITE: Dict[str, Any] = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}

_WRITE_IDEMPOTENT: Dict[str, Any] = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

_DESTRUCTIVE: Dict[str, Any] = {
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": True,
}

_DESTRUCTIVE_IDEMPOTENT: Dict[str, Any] = {
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": True,
    "openWorldHint": True,
}

# -- Tool registry ----------------------------------------------------------
# Each entry: (tool_name, title, annotation_preset, handler_function)

_TOOLS: list[tuple[str, str, Dict[str, Any], Callable[..., Any]]] = [
    # Monitors
    ("pup_monitors_list",       "List Monitors",       _READ_ONLY,  monitors.list_monitors),
    ("pup_monitors_get",        "Get Monitor",         _READ_ONLY,  monitors.get_monitor),
    ("pup_monitors_search",     "Search Monitors",     _READ_ONLY,  monitors.search_monitors),
    ("pup_monitors_delete",     "Delete Monitor",      _DESTRUCTIVE, monitors.delete_monitor),
    # Dashboards
    ("pup_dashboards_list",     "List Dashboards",     _READ_ONLY,  dashboards.list_dashboards),
    ("pup_dashboards_get",      "Get Dashboard",       _READ_ONLY,  dashboards.get_dashboard),
    ("pup_dashboards_delete",   "Delete Dashboard",    _DESTRUCTIVE, dashboards.delete_dashboard),
    # Metrics
    ("pup_metrics_query",       "Query Metrics",       _READ_ONLY,  metrics.query_metrics),
    ("pup_metrics_search",      "Search Metrics",      _READ_ONLY,  metrics.search_metrics),
    ("pup_metrics_list",        "List Metrics",        _READ_ONLY,  metrics.list_metrics),
    ("pup_metrics_submit",      "Submit Metric",       _WRITE,      metrics.submit_metric),
    # Logs
    ("pup_logs_search",         "Search Logs",         _READ_ONLY,  logs.search_logs),
    # Events
    ("pup_events_list",         "List Events",         _READ_ONLY,  events.list_events),
    ("pup_events_search",       "Search Events",       _READ_ONLY,  events.search_events),
    ("pup_events_get",          "Get Event",           _READ_ONLY,  events.get_event),
    # Incidents
    ("pup_incidents_list",      "List Incidents",      _READ_ONLY,  incidents.list_incidents),
    ("pup_incidents_get",       "Get Incident",        _READ_ONLY,  incidents.get_incident),
    # SLOs
    ("pup_slos_list",           "List SLOs",           _READ_ONLY,  slos.list_slos),
    ("pup_slos_get",            "Get SLO",             _READ_ONLY,  slos.get_slo),
    ("pup_slos_create",         "Create SLO",          _WRITE,      slos.create_slo),
    ("pup_slos_update",         "Update SLO",          _WRITE_IDEMPOTENT, slos.update_slo),
    ("pup_slos_delete",         "Delete SLO",          _DESTRUCTIVE, slos.delete_slo),
    ("pup_slos_corrections",    "Get SLO Corrections", _READ_ONLY,  slos.get_slo_corrections),
    # Synthetics
    ("pup_synthetics_tests_list",     "List Synthetic Tests",     _READ_ONLY, synthetics.list_tests),
    ("pup_synthetics_tests_get",      "Get Synthetic Test",       _READ_ONLY, synthetics.get_test),
    ("pup_synthetics_tests_search",   "Search Synthetic Tests",   _READ_ONLY, synthetics.search_tests),
    ("pup_synthetics_locations_list", "List Synthetic Locations",  _READ_ONLY, synthetics.list_locations),
    ("pup_synthetics_api_test_create", "Create Synthetic API Test", _WRITE, synthetics.create_api_test),
    ("pup_synthetics_api_test_update", "Update Synthetic API Test", _WRITE_IDEMPOTENT, synthetics.update_api_test),
    ("pup_synthetics_tests_delete",    "Delete Synthetic Tests",    _DESTRUCTIVE, synthetics.delete_test),
    # Downtimes
    ("pup_downtimes_list",      "List Downtimes",      _READ_ONLY,  downtimes.list_downtimes),
    ("pup_downtimes_get",       "Get Downtime",        _READ_ONLY,  downtimes.get_downtime),
    ("pup_downtimes_cancel",    "Cancel Downtime",     _DESTRUCTIVE, downtimes.cancel_downtime),
    # Tags
    ("pup_tags_list",           "List Host Tags",      _READ_ONLY,  tags.list_tags),
    ("pup_tags_get",            "Get Host Tags",       _READ_ONLY,  tags.get_tags),
    ("pup_tags_add",            "Add Host Tags",       _WRITE,      tags.add_tags),
    ("pup_tags_update",         "Update Host Tags",    _WRITE_IDEMPOTENT, tags.update_tags),
    ("pup_tags_delete",         "Delete Host Tags",    _DESTRUCTIVE_IDEMPOTENT, tags.delete_tags),
    # RUM Applications
    ("pup_rum_apps_list",       "List RUM Apps",       _READ_ONLY,  rum.rum_apps_list),
    ("pup_rum_apps_get",        "Get RUM App",         _READ_ONLY,  rum.rum_app_get),
    ("pup_rum_apps_create",     "Create RUM App",      _WRITE,      rum.rum_app_create),
    ("pup_rum_apps_update",     "Update RUM App",      _WRITE_IDEMPOTENT, rum.rum_app_update),
    ("pup_rum_apps_delete",     "Delete RUM App",      _DESTRUCTIVE, rum.rum_app_delete),
    # RUM Metrics
    ("pup_rum_metrics_list",    "List RUM Metrics",    _READ_ONLY,  rum.rum_metrics_list),
    ("pup_rum_metrics_get",     "Get RUM Metric",      _READ_ONLY,  rum.rum_metric_get),
    ("pup_rum_metrics_create",  "Create RUM Metric",   _WRITE,      rum.rum_metric_create),
    ("pup_rum_metrics_update",  "Update RUM Metric",   _WRITE_IDEMPOTENT, rum.rum_metric_update),
    ("pup_rum_metrics_delete",  "Delete RUM Metric",   _DESTRUCTIVE, rum.rum_metric_delete),
    # RUM Retention Filters
    ("pup_rum_retention_filters_list",   "List RUM Retention Filters",   _READ_ONLY, rum.rum_retention_filters_list),
    ("pup_rum_retention_filters_get",    "Get RUM Retention Filter",     _READ_ONLY, rum.rum_retention_filter_get),
    ("pup_rum_retention_filters_create", "Create RUM Retention Filter",  _WRITE,     rum.rum_retention_filter_create),
    ("pup_rum_retention_filters_update", "Update RUM Retention Filter",  _WRITE_IDEMPOTENT, rum.rum_retention_filter_update),
    ("pup_rum_retention_filters_delete", "Delete RUM Retention Filter",  _DESTRUCTIVE, rum.rum_retention_filter_delete),
    # RUM Sessions
    ("pup_rum_sessions_list",   "List RUM Sessions",   _READ_ONLY,  rum.rum_sessions_list),
    ("pup_rum_sessions_search", "Search RUM Sessions", _READ_ONLY,  rum.rum_sessions_search),
    # RUM Playlists
    ("pup_rum_playlists_list",  "List RUM Playlists",  _READ_ONLY,  rum.rum_playlists_list),
    ("pup_rum_playlists_get",   "Get RUM Playlist",    _READ_ONLY,  rum.rum_playlist_get),
    # RUM Heatmaps
    ("pup_rum_heatmaps_query",  "Query RUM Heatmap",   _READ_ONLY,  rum.rum_heatmap_query),
    # Users
    ("pup_users_list",          "List Users",          _READ_ONLY,  users.list_users),
    ("pup_users_get",           "Get User",            _READ_ONLY,  users.get_user),
    ("pup_roles_list",          "List Roles",          _READ_ONLY,  users.list_roles),
]

for tool_name, title, hints, handler in _TOOLS:
    mcp.tool(name=tool_name, annotations={"title": title, **hints})(handler)


if __name__ == "__main__":
    mcp.run()
