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
docker compose -f docker-compose-dev.yml down
```

### API usage

The application listens on port `8080` inside each container. The Docker demo
publishes the manager at host port `8081` and its two workers at host ports
`8082` and `8083`. Every node exposes `GET /health` and `GET /info`. Manager
and worker nodes also expose `GET /status`, which adds their peer tables to the
base node info.

```bash
# Base info shared by all nodes
curl http://localhost:8081/health
curl http://localhost:8081/info

# Manager node: node info + known peer managers + overseen workers
curl http://localhost:8081/status

# Worker node: node info + overseeing manager's IP
curl http://localhost:8082/status
```

## Design

The Deliverable 1 architecture and design rationale are in the
[design document](docs/design.md).

