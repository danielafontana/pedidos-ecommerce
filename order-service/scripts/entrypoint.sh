#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ]; then
  until pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-orders_user}" -d "${POSTGRES_DB:-orders_db}" > /dev/null 2>&1; do
    echo "Waiting for postgres..."
    sleep 1
  done
fi

if [ -n "$AWS_ENDPOINT_URL" ]; then
  echo "Ensuring SQS queues exist..."
  python - <<'PY'
import os
import time

import boto3
from botocore.exceptions import ClientError

client = boto3.client(
    "sqs",
    endpoint_url=os.environ["AWS_ENDPOINT_URL"],
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
)

queues = [
    os.environ.get("SQS_ORDER_EVENTS_QUEUE", "order-events"),
    os.environ.get("SQS_SAGA_COMMANDS_QUEUE", "saga-commands"),
    os.environ.get("SQS_NOTIFICATION_DISPATCH_QUEUE", "notification-dispatch"),
]

deadline = time.time() + 60
for name in queues:
    while time.time() < deadline:
        try:
            client.get_queue_url(QueueName=name)
            break
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("AWS.SimpleQueueService.NonExistentQueue", "QueueDoesNotExist"):
                client.create_queue(QueueName=name)
                print(f"Created SQS queue: {name}")
                break
            time.sleep(1)
    else:
        raise SystemExit(f"Timed out waiting for SQS queue: {name}")

print("SQS queues ready.")
PY
fi

alembic upgrade head
exec uvicorn order_service.presentation.main:app --host 0.0.0.0 --port 8081
