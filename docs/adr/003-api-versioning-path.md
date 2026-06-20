# ADR-003: Versionamento no path

## Contexto
Enunciado exige API versionada (`/api/v1/...`).

## Decisão
Prefixo `/api/v1` em todos os routers.

## Consequências
- Evolução futura via `/api/v2` sem quebrar clientes

## Alternativas
- Header `Accept-Version` — rejeitado por menor visibilidade.
