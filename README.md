# elvis-botnet

## Overview

Elvis-Botnet is a for education only Peer-to-Peer botnet for a class for my masters degree, CS610 Networking and Security. This code will not have any malicious function. At project completion, it will have the ability for nodes to run and manage communications among one another in a peer to peer fashion. I have a strong interest in the actions of threat intelliegence groups and government agencies to take down malicious botnets. What better way to learn how they work than to build one?

The project will be submitted in 4 installments:

1. Project design and base classes. Establish what makes a "node" and differentiate between manager and worker nodes. Make and deploy a POC that shows the nodes run and respond to HTTP requests with basic information.

2. Node communication. Have nodes be able to receive and action messages. Establish precedence between manager and worker nodes. Manager nodes issue orders and allow for human interface. Need authentication mechanism.

3. Peer list structure and methods - how do you prevent each node from having a list of all other nodes? How do you keep track of how many nodes you have?

4. How can traffic between nodes be secured and/or obscured?

This project will not workaround NAT and will assume that all nodes are available publicly. The output is a Linux binary, no Windows compatibility. 


## Quick start

Requirements: Python 3.11 or newer, Docker, and Docker Compose.

Build the node and start the three-node Docker demo:

```bash
./run.sh
```

Build and run only the standalone binary:

```bash
./scripts/build.sh
./build/elvis-node
```

Stop the Docker demo with `Ctrl+C`. Remove its containers with:

```bash
docker compose -f docker/docker-compose.yml down
```

## Deliverable 1 - Design

A peer-to-peer botnet is an intersting engineering challenge as it needs sufficient mechanisms to act in a distributed manner. A herder (botnet operator) needs a way to issue orders to the botnet. The botnet needs to distribute messages in a way that does not loop. It needs to perform tasks and report that it has done them. I believe a good botnet would not need a "bootstrap" node list (often the downfall of actual threat actor botnets) and instead have a distributed means of keeping track of nodes.

I have chosen a manager/worker pattern. Manager and worker's are child classes of the node class. The node class will incorporate functionality common to all nodes. Which for now I have deemed to be the basis of an API, a healthcheck route, a tracker for received and completed commands, and the ability to return basic node information (IP address, hostname, and other system details of the host).

Herders can interact with manager nodes to issue commands to the botnets. Managers will maintain a list of other managers (but not all managers so the botnet can stay hidden for a lack of a better term). Managers will maintain a list of workers. One manager oversees one set of workers but has no clue about another managers workers. Managers handle communication and connectivity but do not perform actions (so as to hide their presence).

Workers receive and act upon instructions.

All nodes will maintain a queue of instructions. An order will have an originating node and unique ID. A discussion between managers determines if a message has been received and acted upon. Managers will need to track which of their worker nodes have acknowledged the order and also completed the action.

### Architecture (Deliverable 1)

```
                       +----------------+
                       |    Herder      |
                       | (human/CLI)    |
                       +--------+-------+
                                |
                                | HTTP (issues orders, reads status)
                                v
   +----------------------------------------------------------+
   |                        Manager Node                      |
   |   Node (base)                                            |
   |    - GET /health   - GET /info                           |
   |   Manager (extends Node)                                 |
   |    - GET /status  (node info + managers[] + workers[])   |
   +----------------------------------------------------------+
              |                                  |
              | knows of (peer)                  | oversees
              v                                  v
   +--------------------+           +----------------------------+
   |   Manager Node      |          |        Worker Node          |
   |   (another cell,     |          |   Node (base)                |
   |   hidden from this   |         |    - GET /health  - GET /info|
   |   manager's workers) |         |   Worker (extends Node)      |
   +--------------------+           |    - GET /status (+ manager) |
                                     +----------------------------+
                                                 |
                                        oversees (1..N workers,
                                        manager has no visibility
                                        into peer managers' workers)

  Class hierarchy:

      Node
       |-- register_routes() / health() / info() / node_info()
       |-- get_ip_address(), parse_peer_list()
       |
       +-- Manager        (node_type = "manager")
       |     managers: []   peer manager IPs (partial view only)
       |     workers:  []   IPs of workers this manager oversees
       |
       +-- Worker         (node_type = "worker")
             manager_ip: "" IP of the overseeing manager
```

Each manager only knows a subset of other managers (not the whole botnet) and only the workers it directly oversees, so no single node holds a full membership list.


