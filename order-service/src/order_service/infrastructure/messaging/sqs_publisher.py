import json

import boto3

from order_service.domain.ports.repositories import EventPublisher
from order_service.infrastructure.config import settings


class SqsEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self._client = boto3.client(
            "sqs",
            endpoint_url=settings.aws_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self._queue_url = self._get_queue_url(settings.sqs_order_events_queue)

    def _get_queue_url(self, queue_name: str) -> str:
        return self._client.get_queue_url(QueueName=queue_name)["QueueUrl"]

    async def publish(self, event_type: str, payload: dict) -> None:
        body = json.dumps({"eventType": event_type, "payload": payload})
        self._client.send_message(QueueUrl=self._queue_url, MessageBody=body)
