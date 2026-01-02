SHELL := /bin/bash
COMPOSE ?= docker compose
REBUILD_SERVICES ?= dagster-webserver dagster-daemon
DEFAULT_SERVICES ?= postgres minio pgweb dagster-webserver dagster-daemon superset hub
DEFAULT_LOG_SERVICES ?= dagster-webserver dagster-daemon
OBSERVATORY_DIR ?= packages/phlo-observatory/src/phlo_observatory
NPM_OBSERVATORY := npm --prefix $(OBSERVATORY_DIR)
CHECK_CMD := scripts/run-parallel \
	"py lint" "uv run ruff check ." \
	"py format" "uv run ruff format --check ." \
	"py typecheck" "uv run ty check" \
	"ts lint" "$(NPM_OBSERVATORY) run lint" \
	"ts format" "$(NPM_OBSERVATORY) run format -- --check ." \
	"ts typecheck" "$(NPM_OBSERVATORY) exec tsc -- -p $(OBSERVATORY_DIR)/tsconfig.json --noEmit"

# Docker Compose profiles
PROFILE_CORE ?= postgres minio minio-setup dagster-webserver dagster-daemon hub
PROFILE_QUERY ?= nessie nessie-setup trino
PROFILE_BI ?= superset pgweb
PROFILE_DOCS ?= mkdocs
PROFILE_OBSERVABILITY ?= prometheus loki alloy grafana postgres-exporter
PROFILE_API ?= api hasura
PROFILE_CATALOG ?= openmetadata-mysql openmetadata-elasticsearch openmetadata-server openmetadata-ingestion
PROFILE_ALL ?= $(PROFILE_CORE) $(PROFILE_QUERY) $(PROFILE_BI) $(PROFILE_DOCS) $(PROFILE_OBSERVABILITY) $(PROFILE_API) $(PROFILE_CATALOG)

.PHONY: up down stop restart build rebuild pull ps logs exec clean clean-all fresh-start \
	setup install install-dagster health test \
	up-core up-query up-bi up-docs up-observability up-api up-catalog up-all \
	dagster superset hub minio pgweb trino nessie grafana prometheus api hasura mkdocs openmetadata catalog \
	dagster-shell superset-shell postgres-shell minio-shell hub-shell trino-shell nessie-shell \
	health-observability health-api health-catalog \
	check lint lint-sql lint-python format-python typecheck-python \
	lint-ts format-ts typecheck-ts fix-sql

up:
	$(COMPOSE) up -d $(SERVICE)

down:
	$(COMPOSE) down

stop:
	$(COMPOSE) stop $(if $(SERVICE),$(SERVICE),$(DEFAULT_SERVICES))

restart:
	$(COMPOSE) restart $(if $(SERVICE),$(SERVICE),$(DEFAULT_SERVICES))

build:
	$(COMPOSE) build $(SERVICE)

rebuild:
	$(COMPOSE) build --no-cache $(if $(SERVICE),$(SERVICE),$(REBUILD_SERVICES))

pull:
	$(COMPOSE) pull $(SERVICE)

ps:
	$(COMPOSE) ps $(SERVICE)

logs:
	$(COMPOSE) logs -f $(if $(SERVICE),$(SERVICE),$(DEFAULT_LOG_SERVICES))

exec:
	@test -n "$(SERVICE)" || (echo "SERVICE is required, e.g. make exec SERVICE=dagster-webserver CMD=\"bash\""; exit 1)
	@test -n "$(CMD)" || (echo "CMD is required, e.g. make exec SERVICE=dagster-webserver CMD=\"bash\""; exit 1)
	$(COMPOSE) exec $(SERVICE) $(CMD)

clean:
	$(COMPOSE) down --volumes --remove-orphans

clean-all:
	$(COMPOSE) down --volumes --remove-orphans
	docker system prune -f
	rm -rf .venv uv.lock

fresh-start: clean-all setup
	@echo "Clean slate! Ready to start services with 'make up-all' or 'make up-core'"

setup: venv install install-dagster

venv:
	uv venv

install:
	uv pip install -e src

install-dagster:
	cd services/dagster && uv sync

test:
	uv run pytest

dagster:
	@open http://localhost:$${DAGSTER_PORT:-10006}

superset:
	@open http://localhost:$${SUPERSET_PORT:-10007}

hub:
	@open http://localhost:$${APP_PORT:-10009}

minio:
	@open http://localhost:$${MINIO_CONSOLE_PORT:-10002}

pgweb:
	@open http://localhost:$${PGWEB_PORT:-10008}

trino:
	@open http://localhost:$${TRINO_PORT:-10005}

nessie:
	@echo "Nessie REST API: http://localhost:$${NESSIE_PORT:-10003}/api/v1"

grafana:
	@open http://localhost:$${GRAFANA_PORT:-10016}

prometheus:
	@open http://localhost:$${PROMETHEUS_PORT:-10013}

api:
	@open http://localhost:$${API_PORT:-10010}/docs

hasura:
	@open http://localhost:$${HASURA_PORT:-10011}/console

docs:
	@open http://localhost:$${MKDOCS_PORT:-10012}

openmetadata:
	@open http://localhost:$${OPENMETADATA_PORT:-10020}

catalog: openmetadata

# Profile-specific startup targets
up-core:
	$(COMPOSE) up -d $(PROFILE_CORE)

up-query:
	$(COMPOSE) up -d $(PROFILE_QUERY)

up-bi:
	$(COMPOSE) up -d $(PROFILE_BI)

up-docs:
	$(COMPOSE) --profile docs up -d $(PROFILE_DOCS)

up-observability:
	$(COMPOSE) --profile observability up -d $(PROFILE_OBSERVABILITY)

up-api:
	$(COMPOSE) --profile api up -d $(PROFILE_API)

up-catalog:
	$(COMPOSE) --profile catalog up -d $(PROFILE_CATALOG)

up-all:
	$(COMPOSE) up -d $(PROFILE_ALL)

# Health check target
health:
	@echo "=== Service Health Check ==="
	@echo "Postgres:"
	@$(COMPOSE) exec -T postgres pg_isready -U $${POSTGRES_USER:-lake} || echo "  Not ready"
	@echo "MinIO:"
	@curl -sf http://localhost:$${MINIO_API_PORT:-10001}/minio/health/ready > /dev/null && echo "  Ready" || echo "  Not ready"
	@echo "Dagster:"
	@curl -sf http://localhost:$${DAGSTER_PORT:-10006}/server_info > /dev/null && echo "  Ready" || echo "  Not ready"
	@if docker ps --format '{{.Names}}' | grep -q nessie; then \
		echo "Nessie:"; \
		curl -sf http://localhost:$${NESSIE_PORT:-10003}/api/v1/config > /dev/null && echo "  Ready" || echo "  Not ready"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q trino; then \
		echo "Trino:"; \
		curl -sf http://localhost:$${TRINO_PORT:-10005}/v1/info > /dev/null && echo "  Ready" || echo "  Not ready"; \
	fi

# Observability health check
health-observability:
	@echo "=== Observability Stack Health Check ==="
	@if docker ps --format '{{.Names}}' | grep -q prometheus; then \
		echo "Prometheus:"; \
		curl -sf http://localhost:$${PROMETHEUS_PORT:-10013}/-/healthy > /dev/null && echo "  Ready" || echo "  Not ready"; \
	else \
		echo "Prometheus: Not running (use 'make up-observability')"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q loki; then \
		echo "Loki:"; \
		curl -sf http://localhost:$${LOKI_PORT:-10014}/ready > /dev/null && echo "  Ready" || echo "  Not ready"; \
	else \
		echo "Loki: Not running (use 'make up-observability')"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q alloy; then \
		echo "Alloy:"; \
		curl -sf http://localhost:$${ALLOY_PORT:-10015}/-/healthy > /dev/null && echo "  Ready" || echo "  Not ready"; \
	else \
		echo "Alloy: Not running (use 'make up-observability')"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q grafana; then \
		echo "Grafana:"; \
		curl -sf http://localhost:$${GRAFANA_PORT:-10016}/api/health > /dev/null && echo "  Ready" || echo "  Not ready"; \
	else \
		echo "Grafana: Not running (use 'make up-observability')"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q postgres-exporter; then \
		echo "Postgres Exporter:"; \
		curl -sf http://localhost:$${POSTGRES_EXPORTER_PORT:-10017}/ > /dev/null && echo "  Ready" || echo "  Not ready"; \
	else \
		echo "Postgres Exporter: Not running (use 'make up-observability')"; \
	fi

# API health check
health-api:
	@echo "=== API Stack Health Check ==="
	@if docker ps --format '{{.Names}}' | grep -q cascade-api; then \
		echo "FastAPI:"; \
		curl -sf http://localhost:$${API_PORT:-10010}/health > /dev/null && echo "  Ready" || echo "  Not ready"; \
		echo "  Docs: http://localhost:$${API_PORT:-10010}/docs"; \
	else \
		echo "FastAPI: Not running (use 'make up-api')"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q hasura; then \
		echo "Hasura:"; \
		curl -sf http://localhost:$${HASURA_PORT:-10011}/healthz > /dev/null && echo "  Ready" || echo "  Not ready"; \
		echo "  Console: http://localhost:$${HASURA_PORT:-10011}/console"; \
	else \
		echo "Hasura: Not running (use 'make up-api')"; \
	fi

# Catalog health check
health-catalog:
	@echo "=== Data Catalog Health Check ==="
	@if docker ps --format '{{.Names}}' | grep -q openmetadata-server; then \
		echo "OpenMetadata:"; \
		curl -sf http://localhost:$${OPENMETADATA_PORT:-10020}/api/v1/health > /dev/null && echo "  Ready" || echo "  Not ready"; \
		echo "  UI: http://localhost:$${OPENMETADATA_PORT:-10020}"; \
		echo "  Default credentials: admin / admin"; \
	else \
		echo "OpenMetadata: Not running (use 'make up-catalog')"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q openmetadata-mysql; then \
		echo "MySQL:"; \
		docker exec openmetadata-mysql mysqladmin ping -h localhost -u root -p$${OPENMETADATA_MYSQL_ROOT_PASSWORD:-password} 2>/dev/null && echo "  Ready" || echo "  Not ready"; \
	else \
		echo "MySQL: Not running (use 'make up-catalog')"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q openmetadata-elasticsearch; then \
		echo "Elasticsearch:"; \
		curl -sf http://localhost:9200/_cluster/health > /dev/null && echo "  Ready" || echo "  Not ready"; \
	else \
		echo "Elasticsearch: Not running (use 'make up-catalog')"; \
	fi

# Shell access targets
dagster-shell:
	$(COMPOSE) exec dagster-webserver bash

superset-shell:
	$(COMPOSE) exec superset bash

postgres-shell:
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-lake} -d $${POSTGRES_DB:-lakehouse}

minio-shell:
	$(COMPOSE) exec minio sh

hub-shell:
	$(COMPOSE) exec hub sh

trino-shell:
	$(COMPOSE) exec trino trino

nessie-shell:
	$(COMPOSE) exec nessie sh

# Linting targets
lint: lint-python lint-sql

lint-python:
	uv run ruff check .

format-python:
	uv run ruff format --check .

typecheck-python:
	uv run ty check

lint-ts:
	$(NPM_OBSERVATORY) run lint

format-ts:
	$(NPM_OBSERVATORY) run format -- --check .

typecheck-ts:
	$(NPM_OBSERVATORY) exec tsc -- -p $(OBSERVATORY_DIR)/tsconfig.json --noEmit

check:
	@$(CHECK_CMD)

lint-sql:
	uv run sqlfluff lint workflows/transforms/dbt

fix-sql:
	uv run sqlfluff fix workflows/transforms/dbt
