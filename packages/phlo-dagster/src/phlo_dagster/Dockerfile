FROM python:3.11-slim

WORKDIR /opt/dagster

ARG PHLO_VERSION=""

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Install phlo from PyPI (or specific version if provided)
RUN if [ -n "$PHLO_VERSION" ]; then \
        uv pip install --system "phlo[defaults]==$PHLO_VERSION" "phlo-pandera==$PHLO_VERSION" dagster-postgres; \
    else \
        uv pip install --system "phlo[defaults]" phlo-pandera dagster-postgres; \
    fi

# Keep entrypoint outside /opt/dagster so dev volume mounts never hide it.
COPY dagster/entrypoint.sh /usr/local/bin/phlo-dagster-entrypoint.sh
RUN chmod +x /usr/local/bin/phlo-dagster-entrypoint.sh

# Copy workspace configuration
COPY dagster/workspace.yaml /opt/dagster/workspace.yaml
COPY dagster/dagster.yaml /opt/dagster/dagster.yaml

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/phlo-dagster-entrypoint.sh"]
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
