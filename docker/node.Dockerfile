# Runs the prebuilt binary from build/elvis-node (see scripts/build.sh); no build steps here.
FROM debian:trixie-slim

WORKDIR /app
COPY build/elvis-node ./elvis-node

ENTRYPOINT ["/app/elvis-node"]
