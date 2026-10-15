#!/usr/bin/env python3
"""
QuantumSafeVPN — Cloud Gateway Server Entrypoint
=================================================
Runs the production PQC VPN server (ML-KEM-1024 + ML-DSA-65 + AES-256-GCM)
compatible with Docker containers, Cloud VPS, and local testbeds.
"""
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vpn.tunnel_server import start_server

if __name__ == "__main__":
    print("=" * 65)
    print("      QuantumSafeVPN — Cloud Gateway Server Entrypoint")
    print("      NIST FIPS 203 ML-KEM-1024 | FIPS 204 ML-DSA-65")
    print("=" * 65)
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n[!] Cloud server stopped by administrator.")
        sys.exit(0)
