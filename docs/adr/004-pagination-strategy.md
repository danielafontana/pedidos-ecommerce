# ADR-004: Paginação offset

## Contexto
Listagem de pedidos por cliente deve ser paginada.

## Decisão
Paginação `page` (1-based) + `size` (max 100) com metadados `total`, `totalPages`, `hasNext`, `hasPrevious`.

## Consequências
- Implementação simples com SQL `LIMIT/OFFSET`

## Alternativas
- Keyset-based — melhor para escala massiva; offset suficiente para o escopo.
