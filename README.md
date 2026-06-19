# Plataforma de Pedidos E-commerce

Backend do **order-service** em Python/FastAPI com Clean Architecture, Spec-Driven Development, WireMock, LocalStack (SQS), PostgreSQL e Docker.

## Pré-requisitos

- Docker Desktop
- Docker Compose v2

## Subir o ambiente

```bash
# Stack essencial (postgres + wiremock + localstack + order-service)
docker compose --profile core up -d --build

# Com observabilidade (prometheus + grafana + jaeger)
docker compose --profile obs up -d --build
```

## Endpoints

| Serviço | URL |
|---------|-----|
| API | http://localhost:8081 |
| Swagger UI | http://localhost:8081/swagger-ui.html |
| WireMock | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |
| Jaeger | http://localhost:16686 |

## Testar a API

```bash
# Obter token JWT de desenvolvimento
curl http://localhost:8081/dev/token

# Criar pedido (cliente ativo = "1" no WireMock)
curl -X POST http://localhost:8081/api/v1/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"customer_id": "1"}'

# Adicionar item
curl -X POST http://localhost:8081/api/v1/orders/{order_id}/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"product_id": "prod-1", "quantity": 2}'

# Confirmar pedido
curl -X POST http://localhost:8081/api/v1/orders/{order_id}/confirm \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: confirm-001"

# Iniciar pagamento
curl -X POST http://localhost:8081/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"order_id": "<order_id>"}'

# Listar pedidos do cliente
curl "http://localhost:8081/api/v1/orders?customer_id=1&page=1&size=20" \
  -H "Authorization: Bearer <token>"
```

## Desenvolvimento local (sem Docker para o app)

```bash
cd order-service
pip install -e ".[dev]"
pytest tests/unit -v
```

Com cobertura do domínio (mínimo 80%, relatório HTML em `htmlcov/`):

```bash
pytest tests/unit -v
```

Testes de integração (PostgreSQL + WireMock via Testcontainers — requer Docker):

```bash
pytest tests/integration -v --no-cov -m integration
```

## Estrutura

```
├── docker-compose.yml
├── wiremock/mappings/
├── specs/
├── docs/
├── order-service/
│   ├── src/order_service/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/
│   └── tests/
└── PLANO-IMPLEMENTACAO.md
```

## Documentação

- [Plano de implementação](PLANO-IMPLEMENTACAO.md)
- [Arquitetura](docs/architecture.md)
- [ADRs](docs/adr/)
- [Postman](postman/) — collection e environment para testes manuais

## CI/CD (GitHub Actions)

Inspirado na estrutura do [dotflow](https://github.com/dotflow-io/dotflow/tree/master/.github):

| Workflow | Descrição |
|----------|-----------|
| `code-quality.yml` | Ruff, Flake8, MyPy |
| `test.yml` | Testes unitários + cobertura |
| `ci.yml` | Build Docker + scan Trivy |

Rodar localmente (equivalente ao CI):

```bash
cd order-service
pip install -e ".[dev]"
ruff check --config=../.code_quality/ruff.toml src/ tests/
ruff format --check --config=../.code_quality/ruff.toml src/ tests/
flake8 --config=../.code_quality/.flake8 src/ tests/
mypy --config-file=../.code_quality/mypy.ini src/ tests/
pytest tests/unit/ -v --cov=order_service.domain --cov-report=term-missing --cov-fail-under=80
```
