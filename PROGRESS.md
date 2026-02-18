# Progress

## 2026-02-17 -- Added Synthetics API test create, update, and delete tools

- Added 3 new Synthetics tools for API test lifecycle management:
  - `create_api_test` (POST /api/v1/synthetics/tests/api): Create API tests with configurable
    assertions, request settings, locations, options, and tags. Supports all subtypes (http, ssl,
    dns, websocket, tcp, udp, icmp, grpc).
  - `update_api_test` (PUT /api/v1/synthetics/tests/api/{id}): Full replacement update of
    existing API tests.
  - `delete_test` (POST /api/v1/synthetics/tests/delete): Batch delete one or more synthetic
    tests by public ID.
- Input models: `SyntheticsCreateApiTestInput`, `SyntheticsUpdateApiTestInput`,
  `SyntheticsDeleteTestInput` with strict Pydantic validation.
- Shared `_api_test_body` helper for create/update request body construction.
- Registered 3 new tools in server.py (total: 61 tools).
- Added 15 new tests covering JSON body verification, optional field omission, error handling,
  multi-assertion configs, and batch delete scenarios.
- Test suite: 202 tests, all passing.

## 2026-02-17 -- Codebase simplification and consistency pass

- **server.py**: Replaced 90+ repetitive `mcp.tool()` calls with a data-driven
  registry list and annotation presets (`_READ_ONLY`, `_WRITE`, `_WRITE_IDEMPOTENT`,
  `_DESTRUCTIVE`, `_DESTRUCTIVE_IDEMPOTENT`). Registration now iterates `_TOOLS` list.
- **time_parser.py**: Extracted `parse_time_range(from_time, to_time)` helper to
  eliminate the repeated `parse_time` / `now_unix` two-step pattern used in 6+ tools.
- **datadog_client.py**: Removed unnecessary try/except around `response.text` in
  `api_request()` -- httpx `Response.text` never raises.
- **synthetics.py, users.py**: Replaced raw `json.dumps()` calls in `list_locations()`
  and `list_roles()` with `format_output()` for consistency with all other tools.
- **metrics.py**: Removed unused `import time`.
- **synthetics.py**: Removed unused `import json`.
- **users.py**: Removed unused `import json`.
- **slos.py**: Removed redundant `alias="slo_type"` from `SloCreateInput.slo_type`
  (alias was identical to field name).
- All 187 tests pass, no functionality changed.

## 2026-02-17 -- Added README.md

- Created comprehensive README.md documenting the project
- Covers installation, configuration (.env), running the server, Claude Desktop setup
- Documents all 58 tools across 12 domains with description tables
- Explains response formats (JSON/Markdown), time input syntax, project structure
- Includes experimental/AI-generated warning prominently at the top

## 2026-02-17 -- Added SLO create, update, and corrections tools

- Added 3 new SLO tools: create (POST), update (PUT), corrections (GET)
- `create_slo` supports metric, monitor, and time_slice types with optional description, tags, monitor_ids, query
- `update_slo` performs full replacement via PUT /api/v1/slo/{id}
- `get_slo_corrections` lists status corrections with markdown rendering
- Shared `_slo_body` helper for create/update request construction
- Added `_corrections_md` markdown renderer for correction timestamps and categories
- Expanded SLO tests from 5 to 20 (slos.py at 100% coverage)
- Registered 3 new tools in server.py (total: 58 tools)
- Test suite: 187 tests, 94% coverage

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
