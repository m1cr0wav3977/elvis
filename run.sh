#!/usr/bin/env bash
# One-touch entry point: build the node binary, then bring up the demo network.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${ROOT_DIR}/scripts/build.sh"

docker compose -f "${ROOT_DIR}/docker-compose-dev.yml" up --build
