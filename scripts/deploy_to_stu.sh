#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_TMP="$(mktemp -d)"
trap 'rm -f "$LOCAL_TMP/node1.ini" "$LOCAL_TMP/node2.ini" "$LOCAL_TMP/node3.ini"; rmdir "$LOCAL_TMP"' EXIT

python3 - "$ROOT_DIR/configs" "$LOCAL_TMP" <<'PY'
import configparser
import sys
from pathlib import Path

source_dir = Path(sys.argv[1])
output_dir = Path(sys.argv[2])
for filename, port in (("node1.ini", 8081), ("node2.ini", 8082), ("node3.ini", 8083)):
    config = configparser.ConfigParser()
    config.read(source_dir / filename)
    config["node"]["host"] = "0.0.0.0"
    config["node"]["port"] = str(port)
    with (output_dir / filename).open("w") as output:
        config.write(output)
PY

chmod 600 "$LOCAL_TMP/node1.ini" "$LOCAL_TMP/node2.ini" "$LOCAL_TMP/node3.ini"

scp "$ROOT_DIR/build/elvis-node" \
    "$LOCAL_TMP/node1.ini" \
    "$LOCAL_TMP/node2.ini" \
    "$LOCAL_TMP/node3.ini" \
    "$ROOT_DIR/scripts/test.sh" \
    dicesajm@stu.cs.jmu.edu:~/www/

ssh dicesajm@stu.cs.jmu.edu 'bash -s' <<'REMOTE'
set -e
cd "$HOME/www"
chmod +x elvis-node test.sh
chmod 600 node1.ini node2.ini node3.ini

nohup "$HOME/www/elvis-node" --config "$HOME/www/node1.ini" \
    > "$HOME/www/manager.log" 2>&1 < /dev/null &
nohup "$HOME/www/elvis-node" --config "$HOME/www/node2.ini" \
    > "$HOME/www/worker1.log" 2>&1 < /dev/null &
nohup "$HOME/www/elvis-node" --config "$HOME/www/node3.ini" \
    > "$HOME/www/worker2.log" 2>&1 < /dev/null &
REMOTE
