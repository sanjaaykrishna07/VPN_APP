#!/usr/bin/env bash
# ====================================================================
# QuantumSafeVPN — Safe & Non-Destructive Network Rule Cleanup
# ====================================================================

if [ "$EUID" -ne 0 ]; then
  echo "[!] Error: Must be run with root privileges (sudo bash scripts/cleanup_network.sh)"
  exit 1
fi

VPN_SUBNET="10.8.0.0/24"
TUN_IFACE="tun0"
WAN_IFACE=$(ip route show default | awk '{print $5}' | head -n 1)

echo "[*] Cleaning up QuantumSafeVPN NAT and routing rules..."

if [ -n "$WAN_IFACE" ]; then
  iptables -t nat -D POSTROUTING -s "${VPN_SUBNET}" -o "${WAN_IFACE}" -j MASQUERADE 2>/dev/null || true
  iptables -D FORWARD -i "${TUN_IFACE}" -o "${WAN_IFACE}" -j ACCEPT 2>/dev/null || true
  iptables -D FORWARD -i "${WAN_IFACE}" -o "${TUN_IFACE}" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
fi

# Clean up any leftover rules regardless of detected interface
for iface in eth0 wlan0 ens33 enp0s3; do
  iptables -t nat -D POSTROUTING -s "${VPN_SUBNET}" -o "${iface}" -j MASQUERADE 2>/dev/null || true
  iptables -D FORWARD -i "${TUN_IFACE}" -o "${iface}" -j ACCEPT 2>/dev/null || true
  iptables -D FORWARD -i "${iface}" -o "${TUN_IFACE}" -m state --state RELATED,ESTABLISHED 2>/dev/null || true
done

echo "[+] Cleaned up QuantumSafeVPN firewall rules without flushing existing table chains."
