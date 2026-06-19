FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh && pip install --no-cache-dir . "uvicorn[standard]"

ENV PYTHONPATH=/app/src
EXPOSE 8081

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/bin/sh", "./entrypoint.sh"]
