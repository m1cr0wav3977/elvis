class Worker(Node):
    def __init__(self, config: configparser.ConfigParser) -> None:
        super().__init__(config)
        self.logger.info("Worker node initialized.")