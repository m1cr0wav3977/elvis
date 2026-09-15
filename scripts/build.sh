#!/usr/bin/env bash
# Builds src/elvis_botnet into a single ELF binary at build/elvis-node.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
WORK_DIR="${ROOT_DIR}/.pyinstaller"
DIST_NAME="elvis-node"

cd "${ROOT_DIR}"

python3 -m venv .venv-build
source .venv-build/bin/activate

pip install -q -r requirements.txt -r scripts/requirements-build.txt

pyinstaller \
  --onefile \
  --name "${DIST_NAME}" \
  --distpath "${BUILD_DIR}" \
  --workpath "${WORK_DIR}" \
  --specpath "${WORK_DIR}" \
  src/elvis_botnet/main.py

deactivate

echo "Built ${BUILD_DIR}/${DIST_NAME}"
