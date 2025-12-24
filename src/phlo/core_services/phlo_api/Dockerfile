FROM python:3.11-slim

WORKDIR /app

# Install phlo and dependencies
RUN pip install --no-cache-dir phlo fastapi uvicorn pyyaml

# Copy the API application
COPY main.py .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

EXPOSE 4000

CMD ["python", "main.py"]
