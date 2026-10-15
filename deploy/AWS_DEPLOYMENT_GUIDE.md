# QuantumSafe VPN — AWS EC2 Deployment & Production Operations Guide

This guide provides end-to-end instructions for deploying the **QuantumSafe VPN Protocol v2** server on an Amazon Web Services (AWS) Elastic Compute Cloud (EC2) instance, connecting the Android application, achieving full-tunnel routing for HTTPS websites and streaming services, and monitoring traffic in real time.

---

## 1. AWS EC2 Instance Provisioning

### Recommended Instance Specifications
- **AMI**: Ubuntu Server 22.04 LTS (HVM) or Ubuntu Server 24.04 LTS (64-bit x86)
- **Instance Type**: `t3.small` (recommended for AES-NI hardware acceleration and PQC operations) or `t3.micro` (free tier eligible)
- **Storage**: 15–20 GB gp3 EBS Volume
- **Network**: Default VPC with Public IPv4 address enabled

### Security Group Configuration
In the AWS EC2 Console, create or update the instance Security Group with restricted rules:

| Type | Protocol | Port Range | Source | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Custom TCP** | TCP | `7000` | `0.0.0.0/0` | QuantumSafe VPN Protocol v2 Listener |
| **HTTPS** *(optional)* | TCP | `443` | `0.0.0.0/0` | Alternate listener (bypasses restrictive Wi-Fi) |
| **SSH** | TCP | `22` | `My IP` (`<your-ip>/32`) | Secure server administration |
| **Outbound** | All | All | `0.0.0.0/0` | Forwarded internet traffic (NAT Masquerade) |

> [!IMPORTANT]
> Never open SSH (port 22) to `0.0.0.0/0`. Restrict it to your personal IP address.

---

## 2. Server Installation & Deployment

### Step A: Connect to EC2
```bash
ssh -i /path/to/your-key.pem ubuntu@<EC2-PUBLIC-IP>
```

### Step B: Copy Project Files to EC2
From your local terminal, transfer the repository:
```bash
rsync -avz -e "ssh -i /path/to/your-key.pem" \
  --exclude '.gradle' --exclude 'build' --exclude '__pycache__' \
  d:/VPN_APP/ ubuntu@<EC2-PUBLIC-IP>:/opt/quantumsafe-vpn/
```
*(Or clone your Git repository directly onto the instance)*.

### Step C: Execute Automated Deployment Script
On the EC2 instance, execute the setup script with root privileges:
```bash
cd /opt/quantumsafe-vpn
sudo bash deploy/aws_ec2_setup.sh
```

The script automatically:
1. Installs Python 3, pip, python3-venv, iptables, and iproute2.
2. Creates the isolated Python virtual environment.
3. Installs `cryptography`, `kyber-py` (ML-KEM-1024), and `dilithium-py` (ML-DSA-65).
4. Enables Linux kernel IPv4 forwarding (`net.ipv4.ip_forward = 1`).
5. Configures iptables `MASQUERADE` on the default internet gateway interface.
6. Applies **TCP MSS Clamping** (`TCPMSS --clamp-mss-to-pmtu`) to prevent packet fragmentation issues for HTTPS and Netflix streaming.
7. Generates the server's ML-DSA-65 public key identity.
8. Enrolls the Android device (`android-phone`) and displays the security pin.
9. Installs and starts the `quantumsafe-vpn.service` systemd daemon.

---

## 3. Verifying Server Health

Verify that the VPN server is listening and healthy:
```bash
# Check service status
sudo systemctl status quantumsafe-vpn.service

# Verify listening port
sudo ss -tulpn | grep 7000

# View initial server log entries
sudo journalctl -u quantumsafe-vpn.service -n 25 --no-pager
```

---

## 4. Android Client Connection

1. Install `QuantumSafeVPN.apk` on your Android device (Android 8.0+).
2. Open the application.
3. Tap **Configure** or navigate to the **Server** tab:
   - **Server Host / AWS Endpoint IP**: Enter your EC2 Public IPv4 address (e.g., `54.x.x.x`).
   - **Server Port**: `7000`.
   - **Device Identifier**: `android-phone`.
   - **Device Secret Token**: `7cc0af0e368d217a6fd0b2b8259abc8fead9739f43d8be76cd412414ac5d9268` *(or your generated token)*.
   - **Pinned Fingerprint**: Enter your server's SHA-256 fingerprint displayed during setup.
4. Tap **Save Configuration**.
5. Return to the **Home** tab and tap the circular **CONNECT** button.
6. Grant the Android `VpnService` system permission dialog when prompted.
7. Once connected:
   - The status badge displays green **CONNECTED**.
   - Your assigned VPN lease (e.g., `10.8.0.2`) and real-time session duration appear.

---

## 5. Streaming & Browsing Verification (Phase 5)

With the VPN active:
1. **IP Verification**: Open a browser on your phone and visit `https://api.ipify.org` or `https://whatismyipaddress.com`. The reported IP will match your AWS EC2 instance public IP.
2. **DNS Verification**: Visit `https://browserleaks.com/dns` to confirm DNS queries resolve via configured public DNS (1.1.1.1 / 8.8.8.8) with no leaks.
3. **Netflix & Streaming**: Open Netflix, YouTube, or Google. Thanks to TCP MSS Clamping, TLS handshakes and video segments stream without packet drops or hangs.
   *(Note: AWS commercial IP subnets are sometimes cataloged by commercial streaming providers for geo-compliance; ordinary HTTPS websites and video services route with full bandwidth).*

---

## 6. Live Server-Side Network Monitoring (Phase 6)

To observe real-time network activity on a second laptop or terminal:

SSH into your AWS EC2 instance and run the live monitoring tool:
```bash
cd /opt/quantumsafe-vpn
sudo ./venv/bin/python monitoring/live_monitor.py
```

### Observable Telemetry Displayed
- Client connection and disconnection timestamps.
- Client device name (`android-phone`) and leased IP (`10.8.0.2`).
- Protocol mode (`ML-KEM-1024` or `X25519`).
- Outbound destination IP and destination port (e.g., `142.250.x.x:443`).
- **Observable DNS queries** (e.g., `🔍 [DNS QUERY] netflix.com -> Resolver: 1.1.1.1:53`).
- Live transfer volume (bytes transmitted and received).
- Cryptographic replay drops and anti-spoofing diagnostics.

> [!NOTE]
> End-to-end encrypted TLS payloads (passwords, private search terms, HTTPS contents) remain mathematically unreadable. The monitor displays genuine transport layer and DNS metadata only.

---

## 7. Mobile Monitoring Toggle (Phase 7) & Cryptographic Lab (Phase 8)

On the Android application Home screen:
- **Network Inspection: OFF**
  - VPN routes all system traffic silently.
  - Server logs only standard operational telemetry.
- **Network Inspection: ON**
  - Activates diagnostic inspection telemetry.
  - Unlocks the **Shor's Quantum Attack Lab** card.
  - Tapping **TEST ATTACK**:
    - Under **Classical Mode**: Demonstrates how Shor's period-finding algorithm factors a 16-bit key in ~12ms, recovering synthetic test vector plaintext.
    - Under **Quantum-Safe Mode**: Demonstrates how ML-KEM-1024 Module-LWE lattice hardness resists quantum phase estimation, showing `QUANTUM-IMMUNE (0% recovery)`.
