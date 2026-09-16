import configparser
import logging
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify


class Node:
    """Common base for manager and worker nodes."""

    node_type = "node"

    def __init__(self, config: configparser.ConfigParser) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.hostname = socket.gethostname()
        self.static_ip = config["node"].get("ip", "")
        self.started_at = datetime.now(timezone.utc)
        self.commands_received = 0
        self.commands_completed = 0

        self.app = Flask(__name__)
        self.register_routes()

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

    def health(self):
        return jsonify({"status": "ok"})

    def info(self):
        return jsonify(self.node_info())

    def get_ip_address(self) -> str:
        # Route through a UDP socket (no packets sent) to find the outbound interface IP.
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            return socket.gethostbyname(self.hostname)

    def node_info(self) -> dict:
        return {
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