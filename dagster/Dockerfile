FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential git libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/dagster
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV DAGSTER_HOME=/opt/dagster
RUN mkdir -p $DAGSTER_HOME
COPY . /opt/dagster

# Pre-create dirs used by dbt/duckdb
RUN mkdir -p /data/duckdb /data/lake /dbt/profiles

EXPOSE 3000
