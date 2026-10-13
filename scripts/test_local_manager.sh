#!/usr/bin/env bash
set -u

MANAGER_URL="${ELVIS_MANAGER_URL:-http://localhost:8080}"
MANAGER_URL="${MANAGER_URL%/}"

if [[ -z "${ELVIS_ORDER_TOKEN:-}" ]]; then
    printf 'Set ELVIS_ORDER_TOKEN to the manager order token.\n' >&2
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
        --header "Authorization: Bearer ${ELVIS_ORDER_TOKEN}"
        --write-out $'\nHTTP status: %{http_code}\n'
    )

    printf '\n>>> Request\n%s %s\nAuthorization: ******' \
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
order_id="${run_id}-manager"
order="$(printf \
    '{"origin_node_id":"manual-tester","order_id":"%s","kind":"execute","payload":{"command":"echo","arguments":["dry-run test"]}}' \
    "$order_id")"

request GET "$MANAGER_URL/health"
request GET "$MANAGER_URL/info"
request GET "$MANAGER_URL/status"
request POST "$MANAGER_URL/orders" "$order"
request GET "$MANAGER_URL/orders"

exit "$CURL_FAILED"
