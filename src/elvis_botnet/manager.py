from src.elvis_botnet.node import Node

class Manager(Node):
    def __init__(self, config: configparser.ConfigParser) -> None:
        super().__init__(config)
        super().register_routes()
        self.logger.info("Manager node initialized.")

    def register_routes(self):
        super().register_routes()
        self.app.add_url_rule(
            "/status",
            view_func=self.status,
            methods=["GET"]
        )