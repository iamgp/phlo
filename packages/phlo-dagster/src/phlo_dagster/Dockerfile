FROM python:3.12-slim AS phlo-build-context

WORKDIR /opt/phlo-build-context

COPY . .
RUN mkdir -p /opt/phlo-build-context/wheelhouse

FROM python:3.12-slim

WORKDIR /opt/dagster

ARG PHLO_VERSION=""
ARG PHLO_WHEELHOUSE=""

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy only the artifact directory from the context stage; normal generated builds receive an
# empty directory and retain the existing PyPI installation path.
COPY --from=phlo-build-context /opt/phlo-build-context/wheelhouse /opt/phlo-wheelhouse

# Install Phlo from the local wheelhouse when supplied; normal generated stacks retain PyPI behavior.
RUN \
    if [ -n "$PHLO_VERSION" ]; then \
    if [ -n "$PHLO_WHEELHOUSE" ]; then \
        test -d /opt/phlo-wheelhouse; \
        uv pip install --system --no-index --no-deps --reinstall --find-links /opt/phlo-wheelhouse "phlo==$PHLO_VERSION"; \
        uv pip install --system --prerelease explicit --find-links /opt/phlo-wheelhouse "phlo[defaults]==$PHLO_VERSION" dagster-webserver dagster-postgres "psycopg[binary]"; \
        uv pip install --system --no-index --no-deps --reinstall --find-links /opt/phlo-wheelhouse "phlo==$PHLO_VERSION"; \
    else \
        uv pip install --system --no-deps --prerelease explicit "phlo==$PHLO_VERSION"; \
        PHLO_PRERELEASE_REQUIREMENTS="$(python -c 'import importlib.metadata as md, re; print(" ".join(req.split(";")[0].strip() for req in (md.metadata("phlo").get_all("Requires-Dist") or []) if "extra == '\''defaults'\''" in req and re.search(r"(a|b|rc|dev)[0-9]+", req)))')"; \
        uv pip install --system --prerelease explicit "phlo[defaults]==$PHLO_VERSION" $PHLO_PRERELEASE_REQUIREMENTS dagster-webserver dagster-postgres "psycopg[binary]"; \
    fi; \
    else \
        uv pip install --system "phlo[defaults]" dagster-webserver dagster-postgres "psycopg[binary]"; \
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
