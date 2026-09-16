import argparse
import configparser
import logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an elvis-botnet node.")
    parser.add_argument(
        "--config",
        default="config.ini",
        help="Path to the node's .ini config file (default: config.ini)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.StreamHandler()],
    )

    args = parse_args()
    config = configparser.ConfigParser()
    config.read(args.config)

    if config["node"]["type"] == "manager":
        from elvis_botnet.manager import Manager
        node = Manager(config)
    elif config["node"]["type"] == "worker":
        from elvis_botnet.worker import Worker
        node = Worker(config)
    else:
        logging.error("Invalid node type specified in %s", args.config)
        return

    node.run(
        host=config["node"].get("host", "0.0.0.0"),
        port=config["node"].getint("port", 8080),
    )


if __name__ == "__main__":
    main()
