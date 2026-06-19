# ADR-002: Spec-Driven Development

## Contexto
Contratos de API devem ser explícitos e versionados.

## Decisão
OpenAPI 3.1 em `specs/openapi/` como fonte da verdade; FastAPI expõe `/api/v1/openapi.json`.

## Consequências
- Documentação alinhada à implementação
- Base para testes de contrato

## Alternativas
- Code-first sem spec — rejeitado por perder rastreabilidade SDD.
