SHELL := /bin/bash
COMPOSE ?= docker compose
REBUILD_SERVICES ?= dagster-webserver dagster-daemon
DEFAULT_SERVICES ?= postgres minio pgweb dagster-webserver dagster-daemon superset hub
DEFAULT_LOG_SERVICES ?= dagster-webserver dagster-daemon

# Docker Compose profiles
PROFILE_CORE ?= postgres minio minio-setup dagster-webserver dagster-daemon hub
PROFILE_QUERY ?= nessie nessie-setup trino
PROFILE_BI ?= superset pgweb
PROFILE_ALL ?= $(PROFILE_CORE) $(PROFILE_QUERY) $(PROFILE_BI)

.PHONY: up down stop restart build rebuild pull ps logs exec clean clean-all fresh-start \
setup install install-dagster health \
up-core up-query up-bi up-all \
dagster superset hub minio pgweb trino nessie \
dagster-shell superset-shell postgres-shell minio-shell hub-shell trino-shell nessie-shell

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
	rm -rf volumes/minio/* volumes/postgres/* volumes/superset/*
	rm -rf .venv uv.lock

fresh-start: clean-all setup
	@echo "Clean slate! Ready to start services with 'make up-all' or 'make up-core'"

setup: venv install install-dagster

venv:
	uv venv

install:
	uv pip install -e .

install-dagster:
	cd services/dagster && uv venv && uv pip install -e .

dagster:
	open http://localhost:$${DAGSTER_PORT:-3000}

superset:
	open http://localhost:$${SUPERSET_PORT:-8088}

hub:
	open http://localhost:$${APP_PORT:-54321}

minio:
	open http://localhost:$${MINIO_CONSOLE_PORT:-9001}

pgweb:
	open http://localhost:$${PGWEB_PORT:-8081}

trino:
	open http://localhost:$${TRINO_PORT:-8080}

nessie:
	@echo "Nessie REST API: http://localhost:$${NESSIE_PORT:-19120}/api/v1"

# Profile-specific startup targets
up-core:
	$(COMPOSE) up -d $(PROFILE_CORE)

up-query:
	$(COMPOSE) up -d $(PROFILE_QUERY)

up-bi:
	$(COMPOSE) up -d $(PROFILE_BI)

up-all:
	$(COMPOSE) up -d $(PROFILE_ALL)

# Health check target
health:
	@echo "=== Service Health Check ==="
	@echo "Postgres:"
	@$(COMPOSE) exec -T postgres pg_isready -U $${POSTGRES_USER:-lake} || echo "  Not ready"
	@echo "MinIO:"
	@curl -sf http://localhost:$${MINIO_API_PORT:-9000}/minio/health/ready > /dev/null && echo "  Ready" || echo "  Not ready"
	@echo "Dagster:"
	@curl -sf http://localhost:$${DAGSTER_PORT:-3000}/server_info > /dev/null && echo "  Ready" || echo "  Not ready"
	@if docker ps --format '{{.Names}}' | grep -q nessie; then \
		echo "Nessie:"; \
		curl -sf http://localhost:$${NESSIE_PORT:-19120}/api/v1/config > /dev/null && echo "  Ready" || echo "  Not ready"; \
	fi
	@if docker ps --format '{{.Names}}' | grep -q trino; then \
		echo "Trino:"; \
		curl -sf http://localhost:$${TRINO_PORT:-8080}/v1/info > /dev/null && echo "  Ready" || echo "  Not ready"; \
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
