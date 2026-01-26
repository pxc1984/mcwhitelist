FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY bot/pyproject.toml /app/pyproject.toml
COPY bot/uv.lock /app/uv.lock
RUN pip install --no-cache-dir uv \
    && uv venv /app/.venv \
    && uv sync --frozen --no-dev

COPY bot/ /app/bot/
COPY schema/ /app/schema/

CMD ["/app/.venv/bin/python", "-m", "bot.main"]
