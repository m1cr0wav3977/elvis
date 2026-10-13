import configparser
from threading import Event

import pytest

from elvis_botnet.manager import Manager
from elvis_botnet.main import process_orders_periodically
from elvis_botnet.order import Order, OrderStatus, OrderType
from elvis_botnet.worker import Worker


def make_worker() -> Worker:
    config = configparser.ConfigParser()
    config["node"] = {"type": "worker"}
    return Worker(config)


def make_order(order_id: str | None = None) -> Order:
    if order_id is None:
        return Order(
            origin_node_id="manager-1",
            kind=OrderType.EXECUTE,
            payload={"command": "echo", "arguments": ["hello"]},
        )
    return Order(
        origin_node_id="manager-1",
        kind=OrderType.EXECUTE,
        payload={"command": "echo", "arguments": ["hello"]},
        order_id=order_id,
    )


def test_receive_order_requires_configured_token():
    worker = make_worker()
    client = worker.app.test_client()
    response = client.post(
        "/orders",
        json={
            "origin_node_id": "manager-1",
            "kind": "execute",
            "payload": {"command": "echo", "arguments": ["hello"]},
        },
    )

    assert response.status_code == 503
    assert len(worker.order_queue) == 0
    listing = client.get("/orders")
    assert listing.status_code == 503
    assert listing.get_json() == {"error": "order listing unavailable"}


@pytest.mark.parametrize(
    ("node_type", "node_class"),
    [("manager", Manager), ("worker", Worker)],
)
def test_get_orders_returns_pending_and_processing_orders_only(node_type, node_class):
    config = configparser.ConfigParser()
    config["node"] = {"type": node_type}
    config["auth"] = {"order_token": "test-secret"}
    node = node_class(config)
    client = node.app.test_client()
    headers = {"Authorization": "Bearer test-secret"}

    unauthorized = client.get("/orders")
    assert unauthorized.status_code == 401

    first_response = client.post(
        "/orders",
        json={
            "origin_node_id": "manager-1",
            "order_id": "pending-order",
            "kind": "execute",
            "payload": {"command": "echo"},
        },
        headers=headers,
    )
    second_response = client.post(
        "/orders",
        json={
            "origin_node_id": "manager-1",
            "order_id": "processing-order",
            "kind": "http_request",
            "payload": {"method": "GET", "url": "https://example.invalid"},
        },
        headers=headers,
    )
    assert first_response.status_code == second_response.status_code == 202

    processing_order = node.order_queue.get("processing-order")
    assert processing_order is not None
    processing_order.mark_processing()

    listing = client.get("/orders", headers=headers)
    assert listing.status_code == 200
    orders = listing.get_json()["orders"]
    assert [order["order_id"] for order in orders] == [
        "pending-order",
        "processing-order",
    ]
    assert [order["status"] for order in orders] == [
        "pending",
        "processing",
    ]
    assert orders[0]["kind"] == "execute"
    assert orders[0]["payload"] == {"command": "echo"}
    assert orders[0]["origin_node_id"] == "manager-1"
    assert orders[0]["created_at"]

    processing_order.mark_completed()
    completed_listing = client.get("/orders", headers=headers)
    assert completed_listing.status_code == 200
    assert [order["order_id"] for order in completed_listing.get_json()["orders"]] == [
        "pending-order",
    ]


def test_get_orders_returns_empty_list_when_queue_has_no_active_orders():
    config = configparser.ConfigParser()
    config["node"] = {"type": "worker"}
    config["auth"] = {"order_token": "test-secret"}
    worker = Worker(config)

    response = worker.app.test_client().get(
        "/orders",
        headers={"Authorization": "Bearer test-secret"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"orders": []}


def test_receive_order_accepts_environment_token(monkeypatch):
    monkeypatch.setenv("ELVIS_ORDER_TOKEN", "environment-secret")
    worker = make_worker()
    response = worker.app.test_client().post(
        "/orders",
        json={
            "origin_node_id": "manager-1",
            "kind": "execute",
            "payload": {"command": "echo", "arguments": ["hello"]},
        },
        headers={"Authorization": "Bearer " + "environment" + "-secret"},
    )

    assert response.status_code == 202


def test_receive_order_authenticates_and_enqueues_without_processing():
    config = configparser.ConfigParser()
    config["node"] = {"type": "worker"}
    config["auth"] = {"order_token": "test-secret"}
    worker = Worker(config)
    client = worker.app.test_client()
    order_data = {
        "origin_node_id": "manager-1",
        "kind": "http_request",
        "payload": {
            "method": "GET",
            "url": "https://example.invalid/health",
            "headers": {"Accept": "application/json"},
        },
    }

    rejected = client.post("/orders", json=order_data)
    assert rejected.status_code == 401
    assert len(worker.order_queue) == 0

    response = client.post(
        "/orders",
        json=order_data,
        headers={"Authorization": "Bearer test-secret"},
    )

    assert response.status_code == 202
    order_id = response.get_json()["order_id"]
    assert order_id
    assert response.get_json()["status"] == "pending"
    assert len(worker.order_queue) == 1
    received = worker.order_queue.get(order_id)
    assert received is not None
    assert received.origin_node_id == "manager-1"
    assert received.kind is OrderType.HTTP_REQUEST
    assert received.payload == {
        "method": "GET",
        "url": "https://example.invalid/health",
        "headers": {"Accept": "application/json"},
    }
    assert received.status is OrderStatus.PENDING
    assert worker.commands_received == 0
    assert worker.commands_completed == 0


def test_receive_execute_order_accepts_documented_command_shape():
    config = configparser.ConfigParser()
    config["node"] = {"type": "worker"}
    config["auth"] = {"order_token": "test-secret"}
    worker = Worker(config)
    response = worker.app.test_client().post(
        "/orders",
        json={
            "origin_node_id": "manager-1",
            "kind": "execute",
            "payload": {"command": "echo", "arguments": ["hello"]},
        },
        headers={"Authorization": "Bearer " + "test" + "-secret"},
    )

    assert response.status_code == 202
    received = worker.order_queue.get(response.get_json()["order_id"])
    assert received is not None
    assert received.kind is OrderType.EXECUTE
    assert received.payload == {"command": "echo", "arguments": ["hello"]}


@pytest.mark.parametrize(
    "order_data",
    [
        [],
        {"origin_node_id": "", "kind": "execute", "payload": {}},
        {"origin_node_id": "manager-1", "kind": "unsupported", "payload": {}},
        {"origin_node_id": "manager-1", "kind": "execute", "payload": []},
        {"origin_node_id": "manager-1", "kind": "execute", "payload": {"command": ""}},
        {
            "origin_node_id": "manager-1",
            "kind": "execute",
            "payload": {"command": "echo", "arguments": "hello"},
        },
        {
            "origin_node_id": "manager-1",
            "kind": "http_request",
            "payload": {"method": "TRACE", "url": "https://example.invalid"},
        },
        {
            "origin_node_id": "manager-1",
            "kind": "http_request",
            "payload": {"method": "GET", "url": "file:///etc/passwd"},
        },
        {
            "origin_node_id": "manager-1",
            "kind": "execute",
            "payload": {"command": "echo"},
            "unexpected": True,
        },
    ],
)
def test_receive_order_rejects_invalid_bodies_without_enqueuing(order_data):
    config = configparser.ConfigParser()
    config["node"] = {"type": "worker"}
    config["auth"] = {"order_token": "test-secret"}
    worker = Worker(config)
    response = worker.app.test_client().post(
        "/orders",
        json=order_data,
        headers={"Authorization": "Bearer test-secret"},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid order"}
    assert len(worker.order_queue) == 0


def test_receive_order_rejects_duplicate_ids():
    config = configparser.ConfigParser()
    config["node"] = {"type": "worker"}
    config["auth"] = {"order_token": "test-secret"}
    worker = Worker(config)
    client = worker.app.test_client()
    order_data = {
        "origin_node_id": "manager-1",
        "kind": "execute",
        "payload": {"command": "echo"},
        "order_id": "duplicate",
    }
    headers = {"Authorization": "Bearer test-secret"}

    assert client.post("/orders", json=order_data, headers=headers).status_code == 202
    response = client.post("/orders", json=order_data, headers=headers)

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid order"}
    assert len(worker.order_queue) == 1


def test_order_generates_unique_ids_and_tracks_status():
    first = make_order()
    second = make_order()

    assert first.order_id != second.order_id
    assert first.status is OrderStatus.PENDING
    first.mark_processing()
    first.mark_completed()
    assert first.status is OrderStatus.COMPLETED


def test_order_rejects_invalid_status_transitions():
    order = make_order()

    with pytest.raises(ValueError):
        order.mark_completed()

    order.mark_processing()
    with pytest.raises(ValueError):
        order.mark_processing()


def test_queue_rejects_duplicate_order_ids():
    worker = make_worker()
    worker.order_queue.enqueue(make_order("duplicate"))

    with pytest.raises(ValueError, match="already in this queue"):
        worker.order_queue.enqueue(make_order("duplicate"))


def test_node_drains_orders_in_dry_run_and_retains_status(caplog):
    caplog.set_level("INFO")
    worker = make_worker()
    first = make_order("first")
    second = make_order("second")
    worker.order_queue.enqueue(first)
    worker.order_queue.enqueue(second)

    assert worker.process_pending_orders() == 2
    assert worker.process_pending_orders() == 0
    assert len(worker.order_queue) == 0
    assert worker.order_queue.get("first") is first
    assert worker.order_queue.get("second") is second
    assert first.status is OrderStatus.COMPLETED
    assert second.status is OrderStatus.COMPLETED
    assert worker.commands_received == 2
    assert worker.commands_completed == 2
    assert "Dry run: would process order first" in caplog.text


def test_periodic_processor_drains_orders_and_stops(monkeypatch):
    worker = make_worker()
    order = make_order("scheduled")
    worker.order_queue.enqueue(order)
    stop_event = Event()
    process_pending_orders = worker.process_pending_orders

    def process_once():
        processed = process_pending_orders()
        stop_event.set()
        return processed

    monkeypatch.setattr(worker, "process_pending_orders", process_once)
    process_orders_periodically(worker, stop_event, interval_seconds=0.001)

    assert order.status is OrderStatus.COMPLETED
    assert worker.commands_received == 1
    assert worker.commands_completed == 1
