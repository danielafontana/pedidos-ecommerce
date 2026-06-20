import json
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from order_service.domain.datetime_utils import now
from order_service.domain.ports.repositories import EventPublisher
from order_service.infrastructure.messaging.sqs_publisher import (
    SqsEventPublisher,
)
from order_service.infrastructure.persistence.models import OutboxEventModel


class OutboxEventPublisher(EventPublisher):
    def __init__(
        self, session: AsyncSession, sqs_publisher: SqsEventPublisher
    ) -> None:
        self._session = session
        self._sqs = sqs_publisher

    async def publish(self, event_type: str, payload: dict) -> None:
        model = OutboxEventModel(
            id=uuid4(),
            event_type=str(event_type),
            payload=json.dumps(payload),
            published=False,
            created_at=now(),
        )
        self._session.add(model)
        try:
            await self._sqs.publish(event_type, payload)
            model.published = True
        except Exception:
            model.published = False
        await self._session.commit()
