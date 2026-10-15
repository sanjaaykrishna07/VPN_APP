# QuantumSafeVPN — Final Academic Demonstration Protocol

This protocol is structured for live demonstration to faculty, professors, and technical evaluators to prove genuine end-to-end post-quantum cryptographic security and real IP packet forwarding.

---

## 1. Live Demonstration Script

### Step 1: Prove Server Identity & Post-Quantum Keys
Open a terminal on the Linux server:
```bash
ls -la keys/
sha256sum keys/server_mldsa65_public.key
```
*Point out that the server uses persistent ML-DSA-65 (NIST FIPS 204) identity keys.*

### Step 2: Start the VPN Server
```bash
sudo bash scripts/start_server.sh
```
*Demonstrate live stdout logs showing: `net.ipv4.ip_forward = 1`, iptables MASQUERADE activated, and server listening on `0.0.0.0:7000`.*

### Step 3: Demonstrate Server Interface & Routing Tables
Open a second terminal:
```bash
# 1. TUN interface status
ip addr show tun0

# 2. Kernel NAT rules
sudo iptables -t nat -L POSTROUTING -v -n

# 3. Listening socket
ss -tulpn | grep 7000
```

### Step 4: Connect Android Phone over Wi-Fi
1. Open the **QuantumSafeVPN** Android application.
2. Enter the Linux server's LAN IP (`11.12.5.8`) and port (`7000`).
3. Tap **CONNECT TO VPN**.
4. Point out the live handshake log stream on the phone:
   - `[Stage 1/4] Receiving ML-DSA-65 server identity key`
   - `[Stage 2/4] Generating ML-KEM-1024 ephemeral keypair`
   - `[Stage 3/4] Awaiting encapsulated ciphertext & signature`
   - `[+] ML-DSA-65 signature verified! Server authenticated.`
   - `[Stage 4/4] AES-256-GCM session key derived via HKDF-SHA256`
   - `[+] Assigned IP: 10.8.0.2`
   - `[+] ✓ QuantumSafeVPN active! Routing all traffic via tunnel.`

### Step 5: Live Traffic & Wireshark Inspection
On the Linux server, capture traffic on `tun0` and `wlan0`:
```bash
# Observe decrypted packets traversing TUN interface
sudo tcpdump -i tun0 -n -c 10
```
On the phone, open Chrome and search for a website:
- Show that requests flow through `tun0` as raw IP packets.
- Show that encrypted frames on Wi-Fi (port 7000) reveal zero plaintext.

### Step 6: Public IP Shift Verification
- On phone browser, visit `https://ifconfig.me`.
- Verify the displayed IP is identical to the Linux VPN server's external public IP.

### Step 7: Run Automated Security Test Suite
In front of the evaluators, execute:
```bash
python run.py --test
```
*Show that all 6 cryptographic and functional suites pass.*

### Step 8: Run Cryptographic Benchmark
```bash
python benchmark/benchmark.py
```
*Show real empirical execution timings for ML-KEM-1024, ML-DSA-65, HKDF, and AES-256-GCM.*
