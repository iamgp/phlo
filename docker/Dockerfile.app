FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never

RUN pip install --no-cache-dir --upgrade pip uv

COPY services/hub/pyproject.toml ./
RUN uv sync --no-dev

COPY services/hub/app.py .

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 54321

CMD ["python", "app.py"]
