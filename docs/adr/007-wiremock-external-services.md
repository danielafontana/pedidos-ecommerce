# ADR-007: WireMock para serviços externos

## Contexto
Apenas order-service é implementado; demais serviços são simulados.

## Decisão
WireMock standalone via docker-compose; mapeamentos em `wiremock/mappings/`; clientes httpx sem stubs no código.

## Consequências
- Paridade entre dev e testes de integração (Testcontainers)

## Alternativas
- Mocks in-process — proibido pelo enunciado.
