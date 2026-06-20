# ADR-005: Optimistic locking

## Contexto
Requisições concorrentes sobre o mesmo pedido devem ser tratadas.

## Decisão
Coluna `version` em `orders`; incremento a cada mutação; conflito retorna 409.

## Consequências
- Sem locks pessimistas no banco
- Cliente pode retry em caso de conflito

## Alternativas
- Pessimistic locking — rejeitado por reduzir throughput.
