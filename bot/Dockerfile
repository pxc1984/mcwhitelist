FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

COPY bot/pyproject.toml /app/pyproject.toml
COPY bot/uv.lock /app/uv.lock
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY bot/ /app/bot/
COPY schema/ /app/schema/

CMD ["python", "-m", "bot.main"]
