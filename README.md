# elvis-botnet

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

## Project 1 - Design

