import configparser

from flask import jsonify

from elvis_botnet.node import Node


class Worker(Node):
    """Receives and acts on orders issued by a manager."""

    node_type = "worker"

    def __init__(self, config: configparser.ConfigParser) -> None:
        # Primitive peer table: a worker only needs to know its own manager, for now.
        self.manager_ip = config["peers"].get("manager", "") if config.has_section("peers") else ""
        super().__init__(config)
        self.logger.info("Worker node initialized.")

    def register_routes(self):
        super().register_routes()
        self.app.add_url_rule(
            "/status",
            view_func=self.status,
            methods=["GET"]
        )

    def status(self):
        return jsonify({
            **self.node_info(),
            "manager": self.manager_ip,
        })