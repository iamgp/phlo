FROM python:3.11-slim

WORKDIR /opt/dagster

ARG GITHUB_TOKEN

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Install phlo from GitHub (uses token if provided for private repos)
RUN if [ -n "$GITHUB_TOKEN" ]; then \
        uv pip install --system "phlo @ git+https://${GITHUB_TOKEN}@github.com/iamgp/phlo.git" dagster-postgres pyiceberg[s3] trino; \
    else \
        uv pip install --system "phlo @ git+https://github.com/iamgp/phlo.git" dagster-postgres pyiceberg[s3] trino; \
    fi

# Copy workspace configuration
COPY dagster/workspace.yaml /opt/dagster/workspace.yaml
COPY dagster/dagster.yaml /opt/dagster/dagster.yaml

EXPOSE 3000

CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
