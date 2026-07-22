FROM python:3.11-slim AS phlo-build-context

WORKDIR /opt/phlo-build-context

COPY . .
RUN set -eux; \
    if [ -f entrypoint.sh ]; then entrypoint=entrypoint.sh; else entrypoint=phlo-api/entrypoint.sh; fi; \
    install -m 0755 "$entrypoint" /opt/phlo-build-context/phlo-api-entrypoint.sh; \
    mkdir -p /opt/phlo-build-context/wheelhouse

FROM python:3.11-slim

WORKDIR /app

ARG PHLO_VERSION=
ARG PHLO_API_VERSION=
ARG PHLO_WHEELHOUSE=

RUN pip install --no-cache-dir "uv==0.8.13"

COPY --from=phlo-build-context /opt/phlo-build-context/wheelhouse /opt/phlo-wheelhouse

RUN set -eux; \
    PHLO_REQUIREMENT="phlo"; \
    if [ -n "$PHLO_VERSION" ]; then PHLO_REQUIREMENT="phlo==$PHLO_VERSION"; fi; \
    PHLO_API_REQUIREMENT="phlo-api"; \
    if [ -n "$PHLO_API_VERSION" ]; then PHLO_API_REQUIREMENT="phlo-api==$PHLO_API_VERSION"; fi; \
    if [ -n "$PHLO_WHEELHOUSE" ]; then \
        test -d /opt/phlo-wheelhouse; \
        uv pip install --system --no-index --no-deps --reinstall --find-links /opt/phlo-wheelhouse "$PHLO_REQUIREMENT" "$PHLO_API_REQUIREMENT"; \
        uv pip install --system --prerelease explicit --find-links /opt/phlo-wheelhouse "$PHLO_REQUIREMENT" "$PHLO_API_REQUIREMENT"; \
        uv pip install --system --no-index --no-deps --reinstall --find-links /opt/phlo-wheelhouse "$PHLO_REQUIREMENT" "$PHLO_API_REQUIREMENT"; \
    elif [ -n "$PHLO_VERSION" ]; then \
        uv pip install --system --prerelease explicit "$PHLO_REQUIREMENT" "$PHLO_API_REQUIREMENT"; \
    else \
        uv pip install --system phlo "$PHLO_API_REQUIREMENT"; \
    fi

COPY --from=phlo-build-context /opt/phlo-build-context/phlo-api-entrypoint.sh /usr/local/bin/phlo-api-entrypoint.sh

RUN groupadd --system phlo \
    && useradd --system --gid phlo --home-dir /app --no-create-home phlo \
    && chown -R phlo:phlo /app

USER phlo

EXPOSE 4000

ENTRYPOINT ["/usr/local/bin/phlo-api-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "phlo_api.main:app", "--host", "0.0.0.0", "--port", "4000"]
