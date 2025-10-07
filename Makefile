.PHONY: up down rebuild logs dagster superset

up:
	docker compose up -d

down:
	docker compose down

rebuild:
	docker compose build --no-cache dagster-webserver dagster-daemon

logs:
	docker compose logs -f dagster-webserver dagster-daemon

dagster:
	open http://localhost:$${DAGSTER_PORT:-3000}

superset:
	open http://localhost:$${SUPERSET_PORT:-8088}
