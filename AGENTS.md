# Agents Configuration for Phlo

Guidelines for AI agents and developers working on the Phlo codebase.

## Development Philosophy

- Early development: no users, no backward compatibility concerns
- Keep code clean and organized; aim for zero technical debt
- Do not create compatibility shims or workarounds
- Implement features properly to scale beyond 1,000 users
- Do not present half-baked solutions
- Do not add placeholders
- Use beads (see below)

## Build/Lint/Test Commands

### Development Setup

```bash
# Install dependencies
uv pip install -e .

# Type checking
basedpyright src/phlo/

# Linting and formatting
ruff check src/phlo/
ruff format src/phlo/
```

### Service Management

```bash
# Start all services
phlo services start

# Stop services
phlo services stop

# View logs
phlo services logs -f dagster-webserver
```

### Testing

```bash
# Run all tests
phlo test

# Run specific tests
phlo test tests/test_ingestion.py

# Unit tests only
phlo test -m unit

# Skip integration tests (no Docker required)
phlo test --local
```

### Asset Operations

```bash
# Materialize asset
phlo materialize dlt_glucose_entries

# Materialize with partition
phlo materialize dlt_glucose_entries --partition 2024-01-01

# Materialize with downstream
phlo materialize dlt_glucose_entries+
```

### dbt Operations

```bash
# Run dbt models
docker exec phlo-dagster-webserver-1 dbt run --select model_name

# Test dbt models
docker exec phlo-dagster-webserver-1 dbt test --select tag:dataset_name

# Compile dbt (required after model changes)
docker exec phlo-dagster-webserver-1 dbt compile
```

## Architecture & Structure

### Core Components

- **Orchestration**: Dagster with assets in `workflows/`
  - `ingestion/` - DLT-based data ingestion with `@phlo_ingestion` decorator
  - `transform/` - dbt integration for SQL transformations
  - `publishing/` - Publishing marts to PostgreSQL for BI
  - `quality/` - Data quality checks with `@phlo_quality` decorator
  - `sensors/` - Branch lifecycle automation (creation, promotion, cleanup)

- **Storage**: MinIO (S3-compatible) + Nessie (Git-like catalog) + Iceberg (table format)
- **Query Engine**: Trino for distributed SQL queries
- **Transform Layer**: dbt with bronze → silver → gold → marts architecture
- **Metadata**: PostgreSQL for operational metadata
- **Configuration**: `src/phlo/config.py` using Pydantic settings from `.env`

## Code Style & Conventions

### Python Standards

- **Version**: Python 3.11+
- **Line length**: 100 characters
- **Type checking**: basedpyright with strict mode
- **Linting**: ruff (E, F, I, N, UP, B, A, C4, SIM rules)
- **Formatting**: ruff format
- **Imports**: Absolute imports only, sorted with ruff

### Naming Conventions

- **Python code**: snake_case for functions, classes, variables
- **Database objects**: lowercase for schemas, tables, columns
- **Asset names**: Descriptive, prefixed by type (e.g., `dlt_glucose_entries`, `publish_daily_aggregates`)
- **Decorator-generated assets**: Follow `dlt_{table_name}` convention

### Code Organization

- **One asset per file** in appropriate subdirectory
- **Pandera schemas** in `workflows/schemas/{domain}.py`
- **Configuration** via environment variables, accessed through `phlo.config.settings`
- **Error handling**: Use Pydantic validation, structured logging
- **No backwards compatibility shims** - clean implementation only

### Dependencies

- **Package manager**: uv (fast Python package installer)
- **Dependencies**: Pinned in `pyproject.toml`
- **Services**: Docker Compose for infrastructure

## Documentation

User-facing documentation is in `docs/`:

- See `docs/guides/developer-guide.md` for decorator usage
- See `docs/reference/cli-reference.md` for CLI commands
- See `docs/getting-started/core-concepts.md` for architecture overview

## beads

bd - Dependency-Aware Issue Tracker

Issues chained together like beads.

GETTING STARTED
bd init Initialize bd in your project
Creates .beads/ directory with project-specific database
Auto-detects prefix from directory name (e.g., myapp-1, myapp-2)

bd init --prefix api Initialize with custom prefix
Issues will be named: api-1, api-2, ...

CREATING ISSUES
bd create "Fix login bug"
bd create "Add auth" -p 0 -t feature
bd create "Write tests" -d "Unit tests for auth" --assignee alice

VIEWING ISSUES
bd list List all issues
bd list --status open List by status
bd list --priority 0 List by priority (0-4, 0=highest)
bd show bd-1 Show issue details

MANAGING DEPENDENCIES
bd dep add bd-1 bd-2 Add dependency (bd-2 blocks bd-1)
bd dep tree bd-1 Visualize dependency tree
bd dep cycles Detect circular dependencies

DEPENDENCY TYPES
blocks Task B must complete before task A
related Soft connection, doesn't block progress
parent-child Epic/subtask hierarchical relationship
discovered-from Auto-created when AI discovers related work

READY WORK
bd ready Show issues ready to work on
Ready = status is 'open' AND no blocking dependencies
Perfect for agents to claim next work!

UPDATING ISSUES
bd update bd-1 --status in_progress
bd update bd-1 --priority 0
bd update bd-1 --assignee bob

CLOSING ISSUES
bd close bd-1
bd close bd-2 bd-3 --reason "Fixed in PR #42"

### Using bv as an AI sidecar

bv is a fast terminal UI for Beads projects (.beads/beads.jsonl). It renders lists/details and precomputes dependency metrics (PageRank, critical path, cycles, etc.) so you instantly see blockers and execution order. For agents, it’s a graph sidecar: instead of parsing JSONL or risking hallucinated traversal, call the robot flags to get deterministic, dependency-aware outputs.

_IMPORTANT: As an agent, you must ONLY use bv with the robot flags, otherwise you'll get stuck in the interactive TUI that's intended for human usage only!_

- bv --robot-help — shows all AI-facing commands.
- bv --robot-insights — JSON graph metrics (PageRank, betweenness, HITS, critical path, cycles) with top-N summaries for quick triage.
- bv --robot-plan — JSON execution plan: parallel tracks, items per track, and unblocks lists showing what each item frees up.
- bv --robot-priority — JSON priority recommendations with reasoning and confidence.
- bv --robot-recipes — list recipes (default, actionable, blocked, etc.); apply via bv --recipe <name> to pre-filter/sort before other flags.
- bv --robot-diff --diff-since <commit|date> — JSON diff of issue changes, new/closed items, and cycles introduced/resolved.

Use these commands instead of hand-rolling graph logic; bv already computes the hard parts so agents can act safely and quickly.
