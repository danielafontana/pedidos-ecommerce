#!/bin/bash
set -e

awslocal sqs create-queue --queue-name order-events
awslocal sqs create-queue --queue-name saga-commands
awslocal sqs create-queue --queue-name notification-dispatch

echo "LocalStack SQS queues created."
