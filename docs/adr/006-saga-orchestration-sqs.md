# ADR-006: Saga orquestrada com SQS

## Contexto
Confirmação envolve múltiplos passos (cliente, catálogo, persistência, eventos).

## Decisão
`OrderSagaOrchestrator` na camada application; eventos via LocalStack SQS; estado em `saga_instances`.

## Consequências
- Compensações explícitas em falha de catálogo
- Rastreabilidade do passo atual da saga

## Alternativas
- Coreografia pura — rejeitada por complexidade de compensação no escopo.
