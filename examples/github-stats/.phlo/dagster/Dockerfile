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
# Note: In development, mount local phlo source to /phlo-dev and it will override
RUN if [ -n "$PHLO_VERSION" ]; then \
        uv pip install --system "phlo==$PHLO_VERSION" dagster-postgres pyiceberg[s3]; \
    else \
        uv pip install --system phlo dagster-postgres pyiceberg[s3]; \
    fi

# Copy workspace configuration
COPY dagster/workspace.yaml /opt/dagster/workspace.yaml
COPY dagster/dagster.yaml /opt/dagster/dagster.yaml

EXPOSE 3000

CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
