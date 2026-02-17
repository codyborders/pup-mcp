# Progress

## 2026-02-17 -- Added RUM (Real User Monitoring) tools

- Added `tools/rum.py` with 20 new tools across 6 RUM subdomains:
  - Applications: list, get, create, update, delete (v2 /rum/applications)
  - Metrics: list, get, create, update, delete (v2 /rum/metrics)
  - Retention Filters: list, get, create, update, delete (v2 /rum/applications/{id}/retention_filters)
  - Sessions: list, search (v2 /rum/events/search)
  - Playlists: list, get (v2 /rum/playlists)
  - Heatmaps: query (v2 /rum/analytics/heatmap)
- Registered all 20 RUM tools in server.py (total: 55 tools)
- Added 42 RUM tests in `tests/unit/test_rum.py`
- Test suite: 172 tests, 93% coverage

## 2026-02-17 -- Restructured project and added comprehensive tests

- Restructured project to follow PYTHON.md conventions: `src/pup_mcp/` layout with `models/`, `services/`, `utils/`, `tools/` subdirectories
- Created `pyproject.toml` with dependencies, dev deps, pytest/black/isort/mypy configuration
- Custom exception hierarchy: `PupMcpError`, `ConfigurationError`, `DatadogApiError`, `TimeParseError`
- Pydantic Settings model (`models/settings.py`) loading from env vars and `.env` file
- Shared models (`models/common.py`): `PaginatedInput`, `ResponseFormat` enum
- Utilities: time parser for relative/absolute/ISO time strings, response formatting with 25K truncation
- Async Datadog API client (`services/datadog_client.py`) with httpx and error handling
- 35 tools across 10 domains in separate modules: monitors, dashboards, metrics, logs, events, incidents, SLOs, synthetics, downtimes, tags, users
- `server.py` entry point registering all tools with FastMCP annotations
- Comprehensive test suite: 130 tests, 93% coverage
  - Unit tests for all 10 tool modules with respx HTTP mocking
  - Tests for settings, exceptions, time parser, formatting, input validation, server registration
- Dependencies: `mcp[cli]`, `httpx`, `pydantic`, `pydantic-settings`
- Dev dependencies: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`, `respx`, `black`, `isort`, `mypy`

## 2026-02-17 -- Initial pup MCP server implementation (superseded)

- Initial flat-file implementation, replaced by structured layout above
