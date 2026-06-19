# ADR-001: Clean Architecture

## Contexto
O enunciado exige separação entre domínio, aplicação e infraestrutura.

## Decisão
Adotar Clean Architecture com pacotes `domain`, `application`, `infrastructure` e `presentation`.

## Consequências
- Regras de negócio testáveis sem framework
- Infraestrutura substituível (WireMock, PostgreSQL, LocalStack)

## Alternativas
- Arquitetura em camadas acopladas ao FastAPI — rejeitada por dificultar testes de domínio.
