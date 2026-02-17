# pup-mcp

> **Warning**: This is a completely experimental implementation, entirely written by Claude Code (Anthropic's AI coding agent). It has not been reviewed or endorsed by Datadog. Use at your own risk.

An MCP (Model Context Protocol) server that exposes Datadog API operations as tools, enabling LLMs to query and manage your Datadog account through natural language.

Inspired by the [pup CLI](https://github.com/DataDog/pup).

## Requirements

- Python >= 3.11
- A Datadog account with API and Application keys

## Installation

```bash
git clone <repo-url> && cd dd-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in the project root:

```
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_application_key
DD_SITE=datadoghq.com
```

`DD_SITE` defaults to `datadoghq.com`. Set it to your region-specific site if needed (e.g. `datadoghq.eu`, `us5.datadoghq.com`).

## Running the Server

```bash
python -m pup_mcp.server
```

Or with the MCP CLI:

```bash
mcp run src/pup_mcp/server.py
```

### Claude Desktop Configuration

Add this to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pup-mcp": {
      "command": "/path/to/dd-mcp/.venv/bin/python",
      "args": ["-m", "pup_mcp.server"],
      "cwd": "/path/to/dd-mcp",
      "env": {
        "DD_API_KEY": "your_api_key",
        "DD_APP_KEY": "your_app_key"
      }
    }
  }
}
```

## Available Tools (58)

All tools are prefixed with `pup_` and support JSON or Markdown response formats.

### Monitors (4 tools)
| Tool | Description |
|------|-------------|
| `pup_monitors_list` | List monitors with optional filtering |
| `pup_monitors_get` | Get a specific monitor by ID |
| `pup_monitors_search` | Search monitors by query string |
| `pup_monitors_delete` | Delete a monitor |

### Dashboards (3 tools)
| Tool | Description |
|------|-------------|
| `pup_dashboards_list` | List all dashboards |
| `pup_dashboards_get` | Get a dashboard by ID |
| `pup_dashboards_delete` | Delete a dashboard |

### Metrics (4 tools)
| Tool | Description |
|------|-------------|
| `pup_metrics_query` | Query metric timeseries data |
| `pup_metrics_search` | Search metrics by name |
| `pup_metrics_list` | List active metrics |
| `pup_metrics_submit` | Submit a metric data point |

### Logs (1 tool)
| Tool | Description |
|------|-------------|
| `pup_logs_search` | Search and filter log entries |

### Events (3 tools)
| Tool | Description |
|------|-------------|
| `pup_events_list` | List events within a time range |
| `pup_events_search` | Search events by query |
| `pup_events_get` | Get a specific event |

### Incidents (2 tools)
| Tool | Description |
|------|-------------|
| `pup_incidents_list` | List incidents |
| `pup_incidents_get` | Get incident details |

### SLOs (6 tools)
| Tool | Description |
|------|-------------|
| `pup_slos_list` | List all SLOs |
| `pup_slos_get` | Get SLO details |
| `pup_slos_create` | Create a new SLO (metric, monitor, or time_slice) |
| `pup_slos_update` | Update an existing SLO (full replacement) |
| `pup_slos_delete` | Delete an SLO |
| `pup_slos_corrections` | Get status corrections for an SLO |

### Synthetics (4 tools)
| Tool | Description |
|------|-------------|
| `pup_synthetics_tests_list` | List synthetic tests |
| `pup_synthetics_tests_get` | Get a synthetic test |
| `pup_synthetics_tests_search` | Search synthetic tests |
| `pup_synthetics_locations_list` | List available test locations |

### Downtimes (3 tools)
| Tool | Description |
|------|-------------|
| `pup_downtimes_list` | List scheduled downtimes |
| `pup_downtimes_get` | Get downtime details |
| `pup_downtimes_cancel` | Cancel a scheduled downtime |

### Tags (5 tools)
| Tool | Description |
|------|-------------|
| `pup_tags_list` | List all host tags |
| `pup_tags_get` | Get tags for a specific host |
| `pup_tags_add` | Add tags to a host |
| `pup_tags_update` | Update tags on a host |
| `pup_tags_delete` | Remove tags from a host |

### Users (3 tools)
| Tool | Description |
|------|-------------|
| `pup_users_list` | List organization users |
| `pup_users_get` | Get user details |
| `pup_roles_list` | List available roles |

### RUM - Real User Monitoring (20 tools)
| Tool | Description |
|------|-------------|
| `pup_rum_apps_list` | List RUM applications |
| `pup_rum_apps_get` | Get a RUM application |
| `pup_rum_apps_create` | Create a RUM application |
| `pup_rum_apps_update` | Update a RUM application |
| `pup_rum_apps_delete` | Delete a RUM application |
| `pup_rum_metrics_list` | List RUM-based metrics |
| `pup_rum_metrics_get` | Get a RUM metric |
| `pup_rum_metrics_create` | Create a RUM metric |
| `pup_rum_metrics_update` | Update a RUM metric |
| `pup_rum_metrics_delete` | Delete a RUM metric |
| `pup_rum_retention_filters_list` | List retention filters for an app |
| `pup_rum_retention_filters_get` | Get a retention filter |
| `pup_rum_retention_filters_create` | Create a retention filter |
| `pup_rum_retention_filters_update` | Update a retention filter |
| `pup_rum_retention_filters_delete` | Delete a retention filter |
| `pup_rum_sessions_list` | List recent RUM sessions |
| `pup_rum_sessions_search` | Search RUM sessions by query |
| `pup_rum_playlists_list` | List RUM playlists |
| `pup_rum_playlists_get` | Get a RUM playlist |
| `pup_rum_heatmaps_query` | Query RUM heatmap data |

## Response Formats

Most read-only tools accept a `response_format` parameter:

- `json` (default) -- raw JSON from the Datadog API
- `markdown` -- human-readable markdown summary

Responses are truncated at 25,000 characters to stay within LLM context limits.

## Time Inputs

Tools that accept time parameters support:

- **Relative**: `5m`, `1h`, `7d`, `1w` (minutes, hours, days, weeks ago)
- **Unix timestamps**: `1700000000`
- **ISO 8601**: `2024-01-15T10:30:00Z`

## Running Tests

```bash
source .venv/bin/activate
pytest --cov=pup_mcp --cov-report=term-missing
```

Current status: 187 tests, 94% coverage.

## Project Structure

```
src/pup_mcp/
  server.py              # FastMCP entry point, tool registration
  exceptions.py          # Custom exception hierarchy
  models/
    settings.py          # Pydantic Settings (env/dotenv config)
    common.py            # Shared models (PaginatedInput, ResponseFormat)
  services/
    datadog_client.py    # Async httpx client for Datadog API
  utils/
    formatting.py        # JSON/Markdown output formatting
    time_parser.py       # Relative/absolute time parsing
  tools/
    monitors.py          # Monitor CRUD
    dashboards.py        # Dashboard CRUD
    metrics.py           # Metric query/search/submit
    logs.py              # Log search
    events.py            # Event list/search/get
    incidents.py         # Incident list/get
    slos.py              # SLO CRUD + corrections
    synthetics.py        # Synthetic test management
    downtimes.py         # Downtime management
    tags.py              # Host tag management
    users.py             # User/role management
    rum.py               # RUM apps/metrics/filters/sessions/playlists/heatmaps
tests/
  conftest.py            # Shared fixtures (env vars, settings)
  unit/                  # Unit tests for all modules
```

## License

This project is not affiliated with or endorsed by Datadog, Inc.
