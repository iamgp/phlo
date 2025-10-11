FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never

RUN pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py .

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 54321

CMD ["python", "app.py"]
