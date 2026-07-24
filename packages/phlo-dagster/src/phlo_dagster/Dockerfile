FROM python:3.12-slim-bookworm AS phlo-build-context

WORKDIR /opt/phlo-build-context

COPY . .
RUN mkdir -p /opt/phlo-build-context/wheelhouse

FROM python:3.12-slim-bookworm

WORKDIR /opt/dagster

ARG PHLO_VERSION=""
ARG PHLO_DBT_VERSION=""
ARG PHLO_WHEELHOUSE=""

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl="$(apt-cache policy curl | awk '/Candidate:/ {print $2}')" \
    git="$(apt-cache policy git | awk '/Candidate:/ {print $2}')" \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "uv==0.8.13"

# Copy only the artifact directory from the context stage; normal generated builds receive an
# empty directory and retain the existing PyPI installation path.
COPY --from=phlo-build-context /opt/phlo-build-context/wheelhouse /opt/phlo-wheelhouse

# Install Phlo from the local wheelhouse when supplied; normal generated stacks retain PyPI behavior.
RUN \
    PHLO_DBT_REQUIREMENT="phlo-dbt"; \
    if [ -n "$PHLO_DBT_VERSION" ]; then PHLO_DBT_REQUIREMENT="phlo-dbt==$PHLO_DBT_VERSION"; fi; \
    if [ -n "$PHLO_VERSION" ]; then \
    if [ -n "$PHLO_WHEELHOUSE" ]; then \
        test -d /opt/phlo-wheelhouse; \
        uv pip install --system --no-index --no-deps --reinstall --find-links /opt/phlo-wheelhouse "phlo==$PHLO_VERSION"; \
        uv pip install --system --prerelease explicit --find-links /opt/phlo-wheelhouse "phlo[defaults]==$PHLO_VERSION" "$PHLO_DBT_REQUIREMENT" dagster-webserver dagster-postgres "psycopg[binary]"; \
        uv pip install --system --no-index --no-deps --reinstall --find-links /opt/phlo-wheelhouse "phlo==$PHLO_VERSION"; \
        if [ -n "$PHLO_DBT_VERSION" ]; then uv pip install --system --no-index --no-deps --reinstall --find-links /opt/phlo-wheelhouse "$PHLO_DBT_REQUIREMENT"; fi; \
    else \
        uv pip install --system --no-deps --prerelease explicit "phlo==$PHLO_VERSION"; \
        PHLO_PRERELEASE_REQUIREMENTS="$(python -c 'import importlib.metadata as md, re; print(" ".join(req.split(";")[0].strip() for req in (md.metadata("phlo").get_all("Requires-Dist") or []) if "extra == '\''defaults'\''" in req and re.search(r"(a|b|rc|dev)[0-9]+", req)))')"; \
        base_requirements=("phlo[defaults]==$PHLO_VERSION" "$PHLO_DBT_REQUIREMENT" dagster-webserver dagster-postgres "psycopg[binary]"); \
        if [ -n "$PHLO_PRERELEASE_REQUIREMENTS" ]; then read -r -a prerelease_requirements <<< "$PHLO_PRERELEASE_REQUIREMENTS"; base_requirements+=("${prerelease_requirements[@]}"); fi; \
        uv pip install --system --prerelease explicit "${base_requirements[@]}"; \
    fi; \
    else \
        uv pip install --system "phlo[defaults]" "$PHLO_DBT_REQUIREMENT" dagster-webserver dagster-postgres "psycopg[binary]"; \
    fi

# Do not retain uv's downloaded archives in the runtime image; they are not needed to run Phlo.
RUN rm -rf /root/.cache/uv

# Keep entrypoint outside /opt/dagster so dev volume mounts never hide it.
COPY dagster/entrypoint.sh /usr/local/bin/phlo-dagster-entrypoint.sh
RUN chmod +x /usr/local/bin/phlo-dagster-entrypoint.sh \
    && groupadd --system phlo \
    && useradd --system --gid phlo --home-dir /opt/dagster --no-create-home phlo \
    && chown -R phlo:phlo /opt/dagster

USER phlo

# Copy workspace configuration
COPY dagster/workspace.yaml /opt/dagster/workspace.yaml
COPY dagster/dagster.yaml /opt/dagster/dagster.yaml

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/phlo-dagster-entrypoint.sh"]
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
