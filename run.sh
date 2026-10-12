#!/usr/bin/env bash
# One-touch entry point: build the node binary, then bring up the demo network.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${ELVIS_ORDER_TOKEN:-}" ]]; then
    ELVIS_ORDER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    printf 'Generated local testing order token (use as a Bearer token):\n%s\n' \
        "$ELVIS_ORDER_TOKEN"
fi
export ELVIS_ORDER_TOKEN

"${ROOT_DIR}/scripts/build.sh"

docker compose -f "${ROOT_DIR}/docker-compose-dev.yml" up --build
