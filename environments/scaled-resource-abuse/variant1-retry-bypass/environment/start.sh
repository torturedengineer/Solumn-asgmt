#!/bin/sh
set -e
mkdir -p "${GATEWAY_DATA_DIR:-/data}"
python3 /opt/pulsewire-gateway/gateway_server.py > /var/log/gateway.log 2>&1 &
# Give the mock provider a moment to bind before the agent/verifier start.
sleep 0.5
tail -f /dev/null
