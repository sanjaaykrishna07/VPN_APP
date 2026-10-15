# QuantumSafeVPN — Linux & Kali Server Setup Guide

This guide describes how to configure the Linux / Kali machine as a production Post-Quantum VPN Server.

---

## 1. Prerequisites
- Linux OS: Kali Linux, Ubuntu 22.04+, Debian 12, or Fedora
- Python 3.10+
- Root / sudo privileges for TUN interface and iptables creation

---

## 2. One-Click Automated Server Provisioning

Run the setup script as root:
```bash
sudo bash deploy/setup_server.sh
```

This script:
1. Enables Linux kernel IPv4 forwarding:
   ```bash
   sysctl -w net.ipv4.ip_forward=1
   ```
2. Detects your physical internet WAN interface (e.g. `eth0`, `wlan0`, `ens33`).
3. Configures iptables `MASQUERADE` specifically for the VPN subnet `10.8.0.0/24`:
   ```bash
   iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o <WAN_IFACE> -j MASQUERADE
   iptables -A FORWARD -i tun0 -o <WAN_IFACE> -j ACCEPT
   iptables -A FORWARD -i <WAN_IFACE> -o tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT
   ```

---

## 3. Starting the Server

### Interactive / Web Dashboard Mode:
```bash
python run.py
```
- Web Dashboard accessible at: `http://<SERVER_LAN_IP>:8000`
- VPN Server Daemon listens on: `0.0.0.0:7000`

### Standalone Daemon Mode:
```bash
sudo python vpn/tunnel_server.py
```

### Systemd Production Background Service:
```bash
sudo cp deploy/quantumsafevpn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now quantumsafevpn.service
sudo systemctl status quantumsafevpn.service
```

---

## 4. Useful Diagnostic Commands

- **Check Server LAN IP**:
  ```bash
  ip -br addr
  ```
- **Verify Listening Port**:
  ```bash
  ss -tulpn | grep 7000
  ```
- **Check IP Forwarding**:
  ```bash
  sysctl net.ipv4.ip_forward
  ```
- **Inspect NAT Rules**:
  ```bash
  sudo iptables -t nat -L -v -n
  ```
- **Monitor Live VPN Tunnel Interface**:
  ```bash
  ip addr show tun0
  sudo tcpdump -i tun0 -n
  ```
