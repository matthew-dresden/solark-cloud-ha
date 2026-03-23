#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="ha-dev"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "ERROR: HA container '${CONTAINER_NAME}' is not running."
  echo "Start it with: make dev-up"
  exit 1
fi

echo "Restarting Home Assistant to pick up changes..."
docker restart "${CONTAINER_NAME}"
echo "HA restarting. Tail logs with: make dev-logs"
