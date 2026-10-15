#!/usr/bin/env bash
# ====================================================================
# QuantumSafeVPN — Safe & Idempotent Linux Network Forwarding & NAT Setup
# ====================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "[!] Error: Must be run with root privileges (sudo bash scripts/setup_network.sh)"
  exit 1
fi

VPN_SUBNET="10.8.0.0/24"
TUN_IFACE="tun0"

echo "[*] Initializing QuantumSafeVPN Network Provisioning..."

# 1. Enable IPv4 Forwarding in Kernel
echo "[*] Enabling net.ipv4.ip_forward..."
sysctl -w net.ipv4.ip_forward=1 >/dev/null
sed -i '/net.ipv4.ip_forward/d' /etc/sysctl.conf 2>/dev/null || true
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf

# 2. Auto-detect default outbound Internet interface
WAN_IFACE=$(ip route show default | awk '{print $5}' | head -n 1)
if [ -z "$WAN_IFACE" ]; then
  echo "[!] Warning: No default route detected. Fallback to eth0."
  WAN_IFACE="eth0"
fi
echo "[+] Detected default WAN interface: ${WAN_IFACE}"

# 3. Add Idempotent iptables MASQUERADE Rule
iptables -t nat -C POSTROUTING -s "${VPN_SUBNET}" -o "${WAN_IFACE}" -j MASQUERADE 2>/dev/null || \
iptables -t nat -A POSTROUTING -s "${VPN_SUBNET}" -o "${WAN_IFACE}" -j MASQUERADE

# 4. Add Forwarding Rules for tun0
iptables -C FORWARD -i "${TUN_IFACE}" -o "${WAN_IFACE}" -j ACCEPT 2>/dev/null || \
iptables -A FORWARD -i "${TUN_IFACE}" -o "${WAN_IFACE}" -j ACCEPT

iptables -C FORWARD -i "${WAN_IFACE}" -o "${TUN_IFACE}" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
iptables -A FORWARD -i "${WAN_IFACE}" -o "${TUN_IFACE}" -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "[+] Linux IP forwarding and NAT MASQUERADE active for ${VPN_SUBNET} -> ${WAN_IFACE}."
