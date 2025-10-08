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

# Set environment variables for dbt
ENV DBT_PROFILES_DIR=/dbt/profiles
ENV POSTGRES_USER=lake
ENV POSTGRES_PASSWORD=lakepass
ENV POSTGRES_DB=lakehouse
ENV MINIO_ROOT_USER=minio
ENV MINIO_ROOT_PASSWORD=minio999

# Generate dbt manifest for Dagster asset loading
WORKDIR /dbt
RUN if [ -f dbt_project.yml ]; then dbt deps --profiles-dir /dbt/profiles || true; fi
RUN if [ -f dbt_project.yml ]; then dbt parse --profiles-dir /dbt/profiles || true; fi

WORKDIR /opt/dagster
EXPOSE 3000
