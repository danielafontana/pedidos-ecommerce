# Arquitetura — Order Service

## Visão geral

Plataforma de pedidos para e-commerce com um microsserviço implementado (`order-service`) e demais serviços simulados via **WireMock**.

## Microsserviços

| Serviço | Responsabilidade | Implementação |
|---------|------------------|---------------|
| Order Service | Ciclo de vida do pedido, pagamentos, saga | **Implementado** |
| Customer Service | Validação de clientes | WireMock |
| Catalog Service | Produtos, preços, disponibilidade | WireMock |
| Payment Gateway | Processamento de pagamentos | WireMock |
| Notification Service | Notificações de status | WireMock + SQS |

## Bounded Contexts

- **Orders** — pedidos, itens, estados, confirmação
- **Payments** — iniciação, callback, idempotência
- **Integration** — gateways HTTP e mensageria SQS

## Comunicação

- **Síncrona (HTTP):** order-service → WireMock (customer, catalog, payment, notification)
- **Assíncrona (SQS/LocalStack):** eventos `OrderConfirmed`, `PaymentApproved`, `PaymentRejected`, `OrderCancelled`

## Clean Architecture

```
presentation → application → domain ← infrastructure
```

## ADRs

| ADR | Título |
|-----|--------|
| [001](adr/001-clean-architecture.md) | Clean Architecture |
| [002](adr/002-spec-driven-development.md) | Spec-Driven Development |
| [003](adr/003-api-versioning-path.md) | Versionamento no path |
| [004](adr/004-pagination-strategy.md) | Paginação |
| [005](adr/005-optimistic-locking.md) | Optimistic locking |
| [006](adr/006-saga-orchestration-sqs.md) | Saga orquestrada + SQS |
| [007](adr/007-wiremock-external-services.md) | WireMock para serviços externos |
| [008](adr/008-idempotency-strategy.md) | Idempotência |
| [009](adr/009-docker-postgres-local.md) | Docker + PostgreSQL local |
