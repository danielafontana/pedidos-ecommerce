# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install . "uvicorn[standard]"

FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh

ENV PYTHONPATH=/app/src
EXPOSE 8081

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/bin/sh", "./entrypoint.sh"]
