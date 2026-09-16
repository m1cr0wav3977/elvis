import configparser

from flask import jsonify

from elvis_botnet.node import Node


class Manager(Node):
    """Issues orders and tracks worker/peer manager acknowledgement (herder-facing node)."""

    node_type = "manager"

    def __init__(self, config: configparser.ConfigParser) -> None:
        # Peer managers and overseen workers, tracked separately per the design doc.
        self.managers = self.parse_peer_list(config, "managers")
        self.workers = self.parse_peer_list(config, "workers")
        super().__init__(config)
        self.logger.info("Manager node initialized.")

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
            "managers": self.managers,
            "workers": self.workers,
        })