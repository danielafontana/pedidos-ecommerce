from uuid import UUID

from order_service.domain.ports.repositories import SagaRepository


async def compensate_customer_validation_failure(
    saga_repo: SagaRepository,
    saga_id: UUID,
    order_id: UUID,
) -> None:
    await saga_repo.save_instance(
        saga_id,
        order_id,
        "VALIDATE_CUSTOMER",
        "FAILED",
        {"reason": "customer_invalid"},
    )


async def compensate_catalog_validation_failure(
    saga_repo: SagaRepository,
    saga_id: UUID,
    order_id: UUID,
) -> None:
    await saga_repo.save_instance(
        saga_id,
        order_id,
        "VALIDATE_CATALOG",
        "COMPENSATED",
        {"action": "keep_draft"},
    )
