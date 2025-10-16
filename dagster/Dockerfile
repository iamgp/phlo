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

# Create dbt startup script
RUN echo '#!/bin/bash\n\
echo "Setting up dbt..."\n\
cd /dbt\n\
if [ -f dbt_project.yml ]; then\n\
    echo "Installing dbt dependencies..."\n\
    dbt deps --profiles-dir /dbt/profiles || echo "dbt deps failed, continuing..."\n\
    echo "Compiling dbt project..."\n\
    dbt compile --profiles-dir /dbt/profiles || echo "dbt compile failed, continuing..."\n\
else\n\
    echo "dbt_project.yml not found, skipping dbt setup"\n\
fi\n\
echo "Starting Dagster..."\n\
cd /opt/dagster\n\
exec "$@"' > /usr/local/bin/start-dagster.sh && chmod +x /usr/local/bin/start-dagster.sh

WORKDIR /opt/dagster
EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/start-dagster.sh"]
