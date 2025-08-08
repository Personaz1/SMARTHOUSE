#!/usr/bin/env bash
set -euo pipefail

cd /Users/stefan/SMARTHOUSE

echo "==> Up core stack"
docker compose up -d mosquitto sim minio prometheus grafana core
sleep 6

echo "==> MinIO init bucket (idempotent)"
docker run --rm --network=smarthouse_default --entrypoint=/bin/sh minio/mc -c 