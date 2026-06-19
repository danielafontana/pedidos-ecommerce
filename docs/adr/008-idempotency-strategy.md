# ADR-008: Idempotência

## Contexto
Confirmação, pagamento e webhook devem ser idempotentes.

## Decisão
Header `Idempotency-Key` + tabela `idempotency_keys` com hash do payload.

## Consequências
- Cliques repetidos não duplicam efeitos
- Conflito de chave com payload diferente retorna 409

## Alternativas
- Apenas deduplicação em memória — rejeitada por não sobreviver a restarts.
