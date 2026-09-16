import configparser
import logging

def main() -> None:

    logging.basicConfig(                                     
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[   
                logging.StreamHandler()                
            ]
    )

    config = configparser.ConfigParser()
    config.read("config.ini")

    global node
    if config["node"]["type"] == "manager":
        from src.elvis_botnet.manager import Manager
        node = ManagerNode(config)
    elif config["node"]["type"] == "worker":
        from src.elvis_botnet.worker import Worker
        node = WorkerNode(config)
    else:
        logging.error("Invalid node type specified in config.ini")
        return

    node.run(
        host=config["node"].get("host", "0.0.0.0"),
        port=config["node"].getint("port", 8080),
    )

if __name__ == "__main__":
    main()
