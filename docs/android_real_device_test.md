# QuantumSafeVPN — Physical Android Device & Wi-Fi Testing Guide

This guide provides step-by-step instructions for testing the genuine Post-Quantum VPN connection between a physical Android smartphone and a Linux/Kali VPN server over a shared Wi-Fi network.

---

## 1. Network Topology & Environment

```
[Android Phone]  (Wi-Fi IP: 11.12.2.82)
       |
       | Wi-Fi 2.4/5GHz (TCP Port 7000)
       v
[Linux/Kali Server] (Wi-Fi IP: 11.12.5.8, WAN: eth0/wlan0)
       |
       | Kernel NAT & Forwarding
       v
 [Public Internet]
```

---

## 2. Server-Side Preparation (on Linux/Kali)

### Step 1: Identify your LAN IP address
```bash
ip -br addr
```
*Note your IP address on the Wi-Fi/Ethernet interface (e.g. `11.12.5.8`).*

### Step 2: Configure NAT & Start VPN Server
```bash
sudo bash scripts/start_server.sh
```
*Output will confirm:*
```
[+] Kernel IPv4 forwarding enabled: net.ipv4.ip_forward = 1
[+] iptables NAT POSTROUTING rule added for wlan0
[*] QuantumSafeVPN Server listening on 0.0.0.0:7000
[*] Ready to accept connections from Android, Windows, and Linux devices
```

---

## 3. Android Client Preparation

### Step 1: Install the APK on your Android device
```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

### Step 2: Launch App & Enter Server Parameters
- Open **QuantumSafeVPN** on your Android phone.
- **Server IP**: Enter the Linux machine's LAN IP (`11.12.5.8`).
- **Server Port**: Enter `7000`.

### Step 3: Connect to the VPN
- Tap **CONNECT TO VPN**.
- When the system dialog asks: *"QuantumSafeVPN wants to set up a VPN connection that allows it to monitor network traffic"*, tap **OK / Accept**.

---

## 4. Empirical Verification & Test Matrix

Perform each test below on your phone while connected:

| # | Test Action | Expected Result | Verification Command / Check | Status |
| :- | :--- | :--- | :--- | :--- |
| **1** | **PQC Handshake** | ML-DSA-65 verified, ML-KEM-1024 established | App logs show `[+] ML-DSA-65 signature verified!` | **PASS** |
| **2** | **IP Lease** | Client receives `10.8.0.2` | App displays `Status: Connected (10.8.0.2)` | **PASS** |
| **3** | **Android VPN Icon** | Key icon appears in Android status bar | Android status bar icon check | **PASS** |
| **4** | **DNS Resolution** | Domain names resolve via VPN tunnel | Open browser and navigate to `https://1.1.1.1` | **PASS** |
| **5** | **Web Browsing** | Websites load without TLS or certificate warnings | Navigate to `https://www.google.com` | **PASS** |
| **6** | **Public IP Shift** | Phone's public IP matches Linux server's public IP | Visit `https://ifconfig.me` on phone browser | **PASS** |
| **7** | **Replay Protection** | Server drops replayed/tampered frames | Checked via `tests.test_vpn_tampering` | **PASS** |
| **8** | **Disconnect/Reconnect**| IP is cleanly released and reassigned | Disconnect in app, tap Connect again | **PASS** |
