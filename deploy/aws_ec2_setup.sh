#!/usr/bin/env bash
# ==============================================================================
# QuantumSafeVPN — Complete AWS EC2 Server Setup & Deployment Script (Phase 3)
# ==============================================================================
# Supported OS: Ubuntu 22.04 LTS / 24.04 LTS / Debian 12 / Amazon Linux 2023
#
# Usage on fresh AWS EC2 instance:
#   sudo bash deploy/aws_ec2_setup.sh
# ==============================================================================

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run as root: sudo bash deploy/aws_ec2_setup.sh"
  exit 1
fi

APP_DIR="${APP_DIR:-/opt/quantumsafe-vpn}"
VPN_USER="${VPN_USER:-ubuntu}"
VPN_PORT="${VPN_PORT:-7000}"

echo "=============================================================================="
echo "          QUANTUMSAFE VPN — AWS EC2 GATEWAY PROVISIONING"
echo "=============================================================================="

# 1. Update OS & Install System Dependencies
echo "[*] [Step 1/6] Installing Linux system dependencies..."
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-pip python3-venv iptables iproute2 curl ufw
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y python3 python3-pip iptables iproute curl
fi

# 2. Kernel Networking & IP Forwarding
echo "[*] [Step 2/6] Enabling kernel IPv4 forwarding and tuning socket buffers..."
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
cat << 'EOF' > /etc/sysctl.d/99-quantumsafe-vpn.conf
net.ipv4.ip_forward = 1
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
EOF
sysctl -p /etc/sysctl.d/99-quantumsafe-vpn.conf || true

# 3. iptables NAT Masquerade & TCP MSS Clamping
echo "[*] [Step 3/6] Configuring iptables NAT and TCP MSS Clamping for Netflix & HTTPS..."
WAN_IFACE=$(ip route show default | awk '{print $5}' | head -n 1)
echo "[+] Detected default WAN interface: ${WAN_IFACE}"

# Clear previous rules if re-running
iptables -t nat -D POSTROUTING -s 10.8.0.0/24 -o "${WAN_IFACE}" -j MASQUERADE 2>/dev/null || true
iptables -D FORWARD -i tun0 -o "${WAN_IFACE}" -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -i "${WAN_IFACE}" -o tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
iptables -t mangle -D FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu 2>/dev/null || true

# Apply fresh forwarding & MSS clamp
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o "${WAN_IFACE}" -j MASQUERADE
iptables -A FORWARD -i tun0 -o "${WAN_IFACE}" -j ACCEPT
iptables -A FORWARD -i "${WAN_IFACE}" -o tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT
# TCP MSS Clamping prevents packet drops / fragmentation for HTTPS and streaming video
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

# Persist iptables
if command -v iptables-save >/dev/null 2>&1; then
  mkdir -p /etc/iptables
  iptables-save > /etc/iptables/rules.v4
fi

# 4. Prepare Application Directory & Python Virtual Environment
echo "[*] [Step 4/6] Setting up application environment in ${APP_DIR}..."
mkdir -p "${APP_DIR}"
if [ -d "./vpn" ] && [ -d "./pqc" ]; then
  cp -r ./* "${APP_DIR}/"
fi
chown -R root:root "${APP_DIR}"
chmod 700 "${APP_DIR}"

python3 -m venv "${APP_DIR}/venv"
"${APP_DIR}/venv/bin/pip" install --upgrade pip
"${APP_DIR}/venv/bin/pip" install cryptography kyber-py dilithium-py

# 5. Device Enrollment & Server Key Identity
echo "[*] [Step 5/6] Generating ML-DSA-65 identity and enrolling Android client..."
cd "${APP_DIR}"
mkdir -p keys logs
"${APP_DIR}/venv/bin/python" -m pqc.mldsa
"${APP_DIR}/venv/bin/python" -m vpn.manage_clients add android-phone || true

# 6. Install & Start Systemd Daemon
echo "[*] [Step 6/6] Registering systemd daemon (quantumsafe-vpn.service)..."
cat << EOF > /etc/systemd/system/quantumsafe-vpn.service
[Unit]
Description=QuantumSafe VPN Server (Protocol v2)
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
Environment="VPN_SERVER_PORT=${VPN_PORT}"
Environment="VPN_SERVER_HOST=0.0.0.0"
Environment="VPN_KEY_DIR=${APP_DIR}/keys"
Environment="VPN_CLIENTS_FILE=${APP_DIR}/keys/clients.json"
Environment="VPN_EVENT_LOG=${APP_DIR}/logs/events.jsonl"
ExecStart=${APP_DIR}/venv/bin/python ${APP_DIR}/vpn/tunnel_server.py
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable quantumsafe-vpn.service
systemctl restart quantumsafe-vpn.service

echo "=============================================================================="
echo "   ✓ QUANTUMSAFE VPN AWS EC2 DEPLOYMENT COMPLETE!"
echo "=============================================================================="
echo " Server status : $(systemctl is-active quantumsafe-vpn.service)"
echo " Listening on  : 0.0.0.0:${VPN_PORT}"
echo " Service name  : quantumsafe-vpn.service"
echo " Live monitor  : cd ${APP_DIR} && ./venv/bin/python monitoring/live_monitor.py"
echo "=============================================================================="
