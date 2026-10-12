#!/usr/bin/env bash
set -u

MANAGER_URL="${ELVIS_MANAGER_URL:-http://localhost:8081}"
WORKER1_URL="${ELVIS_WORKER1_URL:-http://localhost:8082}"
WORKER2_URL="${ELVIS_WORKER2_URL:-http://localhost:8083}"
MANAGER_URL="${MANAGER_URL%/}"
WORKER1_URL="${WORKER1_URL%/}"
WORKER2_URL="${WORKER2_URL%/}"

if [[ -z "${ELVIS_ORDER_TOKEN:-}" ]]; then
    printf 'Set ELVIS_ORDER_TOKEN to the shared node order token.\n' >&2
    exit 2
fi

CURL_FAILED=0

request() {
    local method="$1"
    local url="$2"
    local data="${3:-}"
    local curl_status
    local -a curl_args=(
        --silent
        --show-error
        --max-time 5
        --request "$method"
        --header "Authorization: Bearer $ELVIS_ORDER_TOKEN"
        --write-out $'\nHTTP status: %{http_code}\n'
    )

    printf '\n>>> Request\n%s %s\nAuthorization: Bearer <ELVIS_ORDER_TOKEN>\n' \
        "$method" "$url"
    if [[ -n "$data" ]]; then
        printf 'Content-Type: application/json\nBody:\n%s\n' "$data"
        curl_args+=(--header "Content-Type: application/json" --data "$data")
    fi

    printf '<<< Response\n'
    if curl "${curl_args[@]}" "$url"; then
        curl_status=0
    else
        curl_status=$?
        CURL_FAILED=1
    fi
    printf 'curl exit status: %s\n' "$curl_status"
}

run_id="manual-$(date +%s%N)-$$"
manager_order_id="${run_id}-manager"
worker1_order_id="${run_id}-worker1"
worker2_order_id="${run_id}-worker2"

manager_order="$(printf \
    '{"origin_node_id":"manual-tester","order_id":"%s","kind":"execute","payload":{"command":"echo","arguments":["dry-run test"]}}' \
    "$manager_order_id")"
worker1_order="$(printf \
    '{"origin_node_id":"manual-tester","order_id":"%s","kind":"http_request","payload":{"method":"GET","url":"https://example.invalid/health","headers":{"Accept":"application/json"}}}' \
    "$worker1_order_id")"
worker2_order="$(printf \
    '{"origin_node_id":"manual-tester","order_id":"%s","kind":"execute","payload":{"command":"echo","arguments":["dry-run test"]}}' \
    "$worker2_order_id")"

request GET "$MANAGER_URL/health"
request GET "$MANAGER_URL/info"
request GET "$MANAGER_URL/status"

request POST "$MANAGER_URL/orders" "$manager_order"
request POST "$WORKER1_URL/orders" "$worker1_order"
request POST "$WORKER2_URL/orders" "$worker2_order"

request GET "$MANAGER_URL/orders"
request GET "$WORKER1_URL/orders"
request GET "$WORKER2_URL/orders"

exit "$CURL_FAILED"
