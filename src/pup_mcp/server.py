"""MCP server entry point -- registers all tools and starts the server."""

import logging

from mcp.server.fastmcp import FastMCP

from pup_mcp.tools import dashboards, downtimes, events, incidents, logs, metrics, monitors, slos, synthetics, tags, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP("pup_mcp")

# ---- Monitors ----
mcp.tool(name="pup_monitors_list", annotations={"title": "List Monitors", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(monitors.list_monitors)
mcp.tool(name="pup_monitors_get", annotations={"title": "Get Monitor", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(monitors.get_monitor)
mcp.tool(name="pup_monitors_search", annotations={"title": "Search Monitors", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(monitors.search_monitors)
mcp.tool(name="pup_monitors_delete", annotations={"title": "Delete Monitor", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})(monitors.delete_monitor)

# ---- Dashboards ----
mcp.tool(name="pup_dashboards_list", annotations={"title": "List Dashboards", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(dashboards.list_dashboards)
mcp.tool(name="pup_dashboards_get", annotations={"title": "Get Dashboard", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(dashboards.get_dashboard)
mcp.tool(name="pup_dashboards_delete", annotations={"title": "Delete Dashboard", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})(dashboards.delete_dashboard)

# ---- Metrics ----
mcp.tool(name="pup_metrics_query", annotations={"title": "Query Metrics", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(metrics.query_metrics)
mcp.tool(name="pup_metrics_search", annotations={"title": "Search Metrics", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(metrics.search_metrics)
mcp.tool(name="pup_metrics_list", annotations={"title": "List Metrics", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(metrics.list_metrics)
mcp.tool(name="pup_metrics_submit", annotations={"title": "Submit Metric", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})(metrics.submit_metric)

# ---- Logs ----
mcp.tool(name="pup_logs_search", annotations={"title": "Search Logs", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(logs.search_logs)

# ---- Events ----
mcp.tool(name="pup_events_list", annotations={"title": "List Events", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(events.list_events)
mcp.tool(name="pup_events_search", annotations={"title": "Search Events", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(events.search_events)
mcp.tool(name="pup_events_get", annotations={"title": "Get Event", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(events.get_event)

# ---- Incidents ----
mcp.tool(name="pup_incidents_list", annotations={"title": "List Incidents", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(incidents.list_incidents)
mcp.tool(name="pup_incidents_get", annotations={"title": "Get Incident", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(incidents.get_incident)

# ---- SLOs ----
mcp.tool(name="pup_slos_list", annotations={"title": "List SLOs", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(slos.list_slos)
mcp.tool(name="pup_slos_get", annotations={"title": "Get SLO", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(slos.get_slo)
mcp.tool(name="pup_slos_delete", annotations={"title": "Delete SLO", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})(slos.delete_slo)

# ---- Synthetics ----
mcp.tool(name="pup_synthetics_tests_list", annotations={"title": "List Synthetic Tests", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(synthetics.list_tests)
mcp.tool(name="pup_synthetics_tests_get", annotations={"title": "Get Synthetic Test", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(synthetics.get_test)
mcp.tool(name="pup_synthetics_tests_search", annotations={"title": "Search Synthetic Tests", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(synthetics.search_tests)
mcp.tool(name="pup_synthetics_locations_list", annotations={"title": "List Synthetic Locations", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(synthetics.list_locations)

# ---- Downtimes ----
mcp.tool(name="pup_downtimes_list", annotations={"title": "List Downtimes", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(downtimes.list_downtimes)
mcp.tool(name="pup_downtimes_get", annotations={"title": "Get Downtime", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(downtimes.get_downtime)
mcp.tool(name="pup_downtimes_cancel", annotations={"title": "Cancel Downtime", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True})(downtimes.cancel_downtime)

# ---- Tags ----
mcp.tool(name="pup_tags_list", annotations={"title": "List Host Tags", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(tags.list_tags)
mcp.tool(name="pup_tags_get", annotations={"title": "Get Host Tags", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(tags.get_tags)
mcp.tool(name="pup_tags_add", annotations={"title": "Add Host Tags", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True})(tags.add_tags)
mcp.tool(name="pup_tags_update", annotations={"title": "Update Host Tags", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(tags.update_tags)
mcp.tool(name="pup_tags_delete", annotations={"title": "Delete Host Tags", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True})(tags.delete_tags)

# ---- Users ----
mcp.tool(name="pup_users_list", annotations={"title": "List Users", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(users.list_users)
mcp.tool(name="pup_users_get", annotations={"title": "Get User", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(users.get_user)
mcp.tool(name="pup_roles_list", annotations={"title": "List Roles", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True})(users.list_roles)


if __name__ == "__main__":
    mcp.run()
