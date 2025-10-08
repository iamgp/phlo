FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential git libpq-dev && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /opt/dagster
COPY pyproject.toml .
RUN uv pip install --system -r pyproject.toml

ENV DAGSTER_HOME=/opt/dagster
RUN mkdir -p $DAGSTER_HOME
COPY . /opt/dagster

# Pre-create dirs used by dbt/duckdb
RUN mkdir -p /data/duckdb /data/lake /dbt/profiles

EXPOSE 3000
