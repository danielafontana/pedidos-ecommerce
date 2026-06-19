import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from order_service.domain.datetime_utils import now
from order_service.domain.ports.repositories import IdempotencyStore, SagaRepository
from order_service.infrastructure.config import settings
from order_service.infrastructure.persistence.models import Base, IdempotencyKeyModel, SagaInstanceModel

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class SqlAlchemyIdempotencyStore(IdempotencyStore):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str, operation: str) -> dict | None:
        result = await self._session.execute(
            select(IdempotencyKeyModel).where(
                IdempotencyKeyModel.key == key,
                IdempotencyKeyModel.operation == operation,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return {"request_hash": model.request_hash, "response": json.loads(model.response_body)}

    async def save(self, key: str, operation: str, request_hash: str, response: dict) -> None:
        model = IdempotencyKeyModel(
            id=uuid4(),
            key=key,
            operation=operation,
            request_hash=request_hash,
            response_body=json.dumps(response),
            created_at=now(),
        )
        self._session.add(model)
        await self._session.commit()


class SqlAlchemySagaRepository(SagaRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_instance(
        self, saga_id: UUID, order_id: UUID, step: str, status: str, payload: dict
    ) -> None:
        result = await self._session.execute(
            select(SagaInstanceModel).where(SagaInstanceModel.order_id == order_id)
        )
        model = result.scalar_one_or_none()
        current = now()
        if model is None:
            model = SagaInstanceModel(
                id=saga_id,
                order_id=order_id,
                current_step=step,
                status=status,
                payload=json.dumps(payload),
                created_at=current,
                updated_at=current,
            )
            self._session.add(model)
        else:
            model.current_step = step
            model.status = status
            model.payload = json.dumps(payload)
            model.updated_at = current
        await self._session.commit()

    async def get_by_order_id(self, order_id: UUID) -> dict | None:
        result = await self._session.execute(
            select(SagaInstanceModel).where(SagaInstanceModel.order_id == order_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return {
            "id": str(model.id),
            "order_id": str(model.order_id),
            "current_step": model.current_step,
            "status": model.status,
            "payload": json.loads(model.payload),
        }
