FROM python:3.11-slim

WORKDIR /app

# Install the same PyPI package versions that generated this stack. Source
# checkouts still copy the local phlo_api package below, but PyPI installs only
# have this package directory as Docker build context.
ARG PHLO_VERSION=
ARG PHLO_API_VERSION=
RUN set -eux; \
    if [ -n "$PHLO_VERSION" ]; then pip install --no-cache-dir "phlo==$PHLO_VERSION"; else pip install --no-cache-dir phlo; fi; \
    if [ -n "$PHLO_API_VERSION" ]; then pip install --no-cache-dir "phlo-api==$PHLO_API_VERSION"; else pip install --no-cache-dir phlo-api; fi

# Copy the API package so `phlo_api.main` is importable.
COPY . /app/phlo_api

ENV PYTHONPATH=/app

EXPOSE 4000

CMD ["python", "-m", "uvicorn", "phlo_api.main:app", "--host", "0.0.0.0", "--port", "4000"]
