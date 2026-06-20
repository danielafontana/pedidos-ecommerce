import json
from typing import Any

import boto3

from order_service.domain.ports.repositories import EventPublisher
from order_service.infrastructure.config import settings


class SqsEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self._client: Any | None = None
        self._queue_url: str | None = None
        self._queue_name = settings.sqs_order_events_queue

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        self._client = boto3.client(
            "sqs",
            endpoint_url=settings.aws_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self._queue_url = self._client.get_queue_url(
            QueueName=self._queue_name
        )["QueueUrl"]

    async def publish(self, event_type: str, payload: dict) -> None:
        self._ensure_client()
        assert self._client is not None
        assert self._queue_url is not None
        body = json.dumps({"eventType": event_type, "payload": payload})
        self._client.send_message(QueueUrl=self._queue_url, MessageBody=body)
