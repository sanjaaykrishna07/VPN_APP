#!/usr/bin/env bash
# ====================================================================
# QuantumSafeVPN — Production Server Startup Script
# ====================================================================

set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "[!] Error: VPN Server requires root privileges to configure TUN and routing."
  echo "    Please run as: sudo bash scripts/start_server.sh"
  exit 1
fi

echo "================================================================="
echo "   Starting QuantumSafeVPN Server (Port 7000)"
echo "================================================================="

# 1. Provision NAT and IP Forwarding
bash "${PROJECT_ROOT}/scripts/setup_network.sh"

# 2. Start VPN Tunnel Server
PYTHON_EXEC="python3"
if [ -f "${PROJECT_ROOT}/venv/bin/python" ]; then
  PYTHON_EXEC="${PROJECT_ROOT}/venv/bin/python"
fi

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
export VPN_SERVER_PORT=7000

echo "[*] Executing ${PYTHON_EXEC} vpn/tunnel_server.py..."
exec "${PYTHON_EXEC}" "${PROJECT_ROOT}/vpn/tunnel_server.py"
