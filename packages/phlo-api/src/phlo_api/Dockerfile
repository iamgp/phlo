FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN pip install --no-cache-dir phlo fastapi uvicorn pyyaml

# Copy the API package so `phlo_api.main` is importable.
COPY . /app/phlo_api

ENV PYTHONPATH=/app

EXPOSE 4000

CMD ["python", "-m", "uvicorn", "phlo_api.main:app", "--host", "0.0.0.0", "--port", "4000"]
