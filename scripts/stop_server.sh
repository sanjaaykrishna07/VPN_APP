#!/usr/bin/env bash
# ====================================================================
# QuantumSafeVPN — Production Server Stop Script
# ====================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "[!] Error: Must be run with root privileges (sudo bash scripts/stop_server.sh)"
  exit 1
fi

echo "[*] Stopping QuantumSafeVPN server processes..."

# Terminate tunnel_server.py processes
pkill -f "vpn/tunnel_server.py" || true

# Cleanup NAT rules
bash "${PROJECT_ROOT}/scripts/cleanup_network.sh"

echo "[+] QuantumSafeVPN server stopped and network rules cleaned up."
