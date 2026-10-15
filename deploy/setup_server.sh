#!/usr/bin/env bash
# ====================================================================
# QuantumSafeVPN — Production Server Setup & NAT Configuration Script
# ====================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run as root (e.g. sudo bash deploy/setup_server.sh)"
  exit 1
fi

echo "================================================================="
echo "   QuantumSafeVPN — Linux Server & NAT Provisioning"
echo "================================================================="

# 1. Enable IPv4 Kernel Forwarding
echo "[*] Enabling net.ipv4.ip_forward..."
sysctl -w net.ipv4.ip_forward=1 || true
touch /etc/sysctl.conf 2>/dev/null || true
sed -i '/net.ipv4.ip_forward/d' /etc/sysctl.conf 2>/dev/null || true
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf 2>/dev/null || true

# 2. Detect WAN Interface
WAN_IFACE=$(ip route show default | awk '{print $5}' | head -n 1)
echo "[+] Detected default WAN interface: ${WAN_IFACE}"

# 3. Setup iptables MASQUERADE
echo "[*] Adding iptables NAT rules for 10.8.0.0/24..."
iptables -t nat -C POSTROUTING -s 10.8.0.0/24 -o "${WAN_IFACE}" -j MASQUERADE 2>/dev/null || \
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o "${WAN_IFACE}" -j MASQUERADE

iptables -C FORWARD -i tun0 -o "${WAN_IFACE}" -j ACCEPT 2>/dev/null || \
iptables -A FORWARD -i tun0 -o "${WAN_IFACE}" -j ACCEPT

iptables -C FORWARD -i "${WAN_IFACE}" -o tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
iptables -A FORWARD -i "${WAN_IFACE}" -o tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "[+] iptables NAT configured successfully."

# 4. Install systemd service if running from /opt/QuantumSafeVPN
if [ -d "/opt/QuantumSafeVPN" ]; then
  cp deploy/quantumsafevpn.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable quantumsafevpn.service
  echo "[+] systemd service quantumsafevpn.service installed & enabled."
fi

echo "================================================================="
echo "   ✓ QuantumSafeVPN Server Ready on port 7000!"
echo "================================================================="
