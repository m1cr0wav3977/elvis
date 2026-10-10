# Deliverable 1 Design

**A demo of the project can be seen by sending a GET request to
https://cs610.catamountcyber.com/ with the health, info, or status route. Only
the manager node is exposed.**

A peer-to-peer botnet is an interesting engineering challenge because it needs
sufficient mechanisms to act in a distributed manner. A herder (botnet
operator) needs a way to issue orders to the botnet. The botnet needs to
distribute messages without looping, perform tasks, and report completion. A
good botnet would not need a bootstrap node list (often the downfall of actual
threat-actor botnets) and instead would have a distributed means of keeping
track of nodes.

The design uses a manager/worker pattern. Manager and Worker are child classes
of Node. Node incorporates functionality common to all nodes: an API,
a health-check route, a tracker for received and completed commands, and basic
node information such as IP address, hostname, and system details.

Herders can interact with manager nodes to issue commands to the botnet.
Managers maintain a partial list of other managers and a list of their own
workers. One manager oversees one set of workers but does not know another
manager's workers. Managers handle communication and connectivity but do not
perform actions. Workers receive and act on instructions.

All nodes maintain a queue of instructions. An order has an originating node
and unique ID. A discussion between managers determines whether a message has
been received and acted on. Managers track which of their worker nodes have
acknowledged the order and completed the action.

## Architecture

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
   |   Manager Node     |           |        Worker Node         |
   |   (another cell,   |           |   Node (base)              |
   |   hidden from this |           |    - GET /health - GET /info|
   |   manager's workers)|          |   Worker (extends Node)    |
   +--------------------+           |    - GET /status (+ manager)|
                                     +----------------------------+
                                                 |
                                        oversees (1..N workers;
                                        manager has no visibility
                                        into peer managers' workers)

  Class hierarchy:

      Node
       |-- register_routes() / health() / info() / node_info()
       |-- get_ip_address(), parse_peer_list()
       |
       +-- Manager        (node_type = "manager")
       |     managers: []  peer manager IPs (partial view only)
       |     workers: []   IPs of workers this manager oversees
       |
       +-- Worker         (node_type = "worker")
             manager_ip: "" IP of the overseeing manager
```

Each manager knows only a subset of other managers and the workers it directly
oversees, so no single node holds a full membership list.
