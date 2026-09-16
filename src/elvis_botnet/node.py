from flask import Flask, jsonify
import logging

class Node:
    def __init__(self, config: configparser.ConfigParser) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.app = Flask(__name__)
        self.register_routes()

    def register_routes(self):
        self.app.add_url_rule(
            "/health",
            view_func=self.health,
            methods=["GET"]
        )

    def health(self):
        return jsonify({"status": "ok"})

    def run(self, **kwargs):
        self.app.run(**kwargs)