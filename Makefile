SHELL := /bin/bash
COMPOSE ?= docker compose
REBUILD_SERVICES ?= dagster-webserver dagster-daemon
DEFAULT_SERVICES ?= postgres minio pgweb dagster-webserver dagster-daemon superset hub
DEFAULT_LOG_SERVICES ?= dagster-webserver dagster-daemon

.PHONY: up down stop restart build rebuild pull ps logs exec clean setup install install-dagster \
dagster superset hub minio pgweb dagster-shell superset-shell postgres-shell \
minio-shell hub-shell

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
