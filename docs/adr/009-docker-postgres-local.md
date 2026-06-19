# ADR-009: Docker + PostgreSQL local

## Contexto
Ambiente local deve ser reproduzível sem instalar dependências na máquina host.

## Decisão
docker-compose com PostgreSQL 16, volume `postgres_data`, healthchecks e Alembic no startup.

## Consequências
- `docker compose --profile core up` sobe stack completa
- Dados persistem entre restarts

## Alternativas
- SQLite local — rejeitado; enunciado exige banco relacional (PostgreSQL).
