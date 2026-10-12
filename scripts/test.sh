#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${ELVIS_MANAGER_URL:-http://localhost:8081}"
BASE_URL="${BASE_URL%/}"

if [[ -z "${ELVIS_ORDER_TOKEN:-}" ]]; then
    printf 'Set ELVIS_ORDER_TOKEN to the manager [auth] order_token.\n' >&2
    exit 2
fi

request_json() {
    local method="$1"
    local path="$2"
    local expected_status="$3"
    local data="${4:-}"
    local response
    local status
    local body
    local curl_args=(
        --silent
        --show-error
        --max-time 5
        --request "$method"
        --write-out $'\n%{http_code}'
    )

    if [[ -n "$data" ]]; then
        curl_args+=(
            --header "Authorization: Bearer ${ELVIS_ORDER_TOKEN}"
            --header "Content-Type: application/json"
            --data "$data"
        )
    fi

    if ! response="$(curl "${curl_args[@]}" "${BASE_URL}${path}")"; then
        printf 'FAIL %s %s: request failed\n' "$method" "$path" >&2
        return 1
    fi

    status="${response##*$'\n'}"
    body="${response%$'\n'*}"
    if [[ "$status" != "$expected_status" ]]; then
        printf 'FAIL %s %s: expected HTTP %s, got %s: %s\n' \
            "$method" "$path" "$expected_status" "$status" "$body" >&2
        return 1
    fi
    if ! jq -e 'type == "object"' <<<"$body" >/dev/null; then
        printf 'FAIL %s %s: expected a JSON object response\n' "$method" "$path" >&2
        return 1
    fi

    printf '%s' "$body"
}

health="$(request_json GET /health 200)"
jq -e '.status == "ok"' <<<"$health" >/dev/null || {
    printf 'FAIL GET /health: expected status=ok\n' >&2
    exit 1
}
printf 'PASS GET /health\n'

info="$(request_json GET /info 200)"
jq -e '.node_type == "manager" and (.node_id | type == "string" and length > 0)' \
    <<<"$info" >/dev/null || {
    printf 'FAIL GET /info: expected manager node info with a node ID\n' >&2
    exit 1
}
node_id="$(jq -er '.node_id' <<<"$info")"
printf 'PASS GET /info\n'

status="$(request_json GET /status 200)"
jq -e '.node_type == "manager" and (.managers | type == "array") and (.workers | type == "array")' \
    <<<"$status" >/dev/null || {
    printf 'FAIL GET /status: expected manager and worker lists\n' >&2
    exit 1
}
printf 'PASS GET /status\n'

order_id="smoke-test-$(date +%s%N)-$$"
order_json="$(jq -cn \
    --arg origin_node_id "$node_id" \
    --arg order_id "$order_id" \
    '{
        origin_node_id: $origin_node_id,
        kind: "execute",
        payload: {command: "echo", arguments: ["dry-run smoke test"]},
        order_id: $order_id
    }')"
accepted="$(request_json POST /orders 202 "$order_json")"
jq -e --arg order_id "$order_id" \
    '.order_id == $order_id and .status == "pending"' \
    <<<"$accepted" >/dev/null || {
    printf 'FAIL POST /orders: response did not acknowledge the queued order\n' >&2
    exit 1
}
printf 'PASS POST /orders (enqueued only; processing is not triggered)\n'
