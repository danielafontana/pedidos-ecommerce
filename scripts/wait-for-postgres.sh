#!/bin/sh
set -e

host="${POSTGRES_HOST:-postgres}"
port="${POSTGRES_PORT:-5432}"
user="${POSTGRES_USER:-orders_user}"
db="${POSTGRES_DB:-orders_db}"

echo "Waiting for PostgreSQL at ${host}:${port}..."
until pg_isready -h "$host" -p "$port" -U "$user" -d "$db" > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is ready."
