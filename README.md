# QuantumSafe VPN — Android Application & Post-Quantum Server

A real, native Android VPN application engineered with Kotlin, Jetpack Compose, Material 3, and Android's `VpnService`, communicating with a Post-Quantum Cryptographic (PQC) VPN server over an authenticated tunnel.

---

## 📦 Deliverables & File Locations

- **Debug APK**: [`dist/QuantumSafe-VPN-debug.apk`](file:///D:/VPN_APP/dist/QuantumSafe-VPN-debug.apk) (19.01 MB)
- **Release APK (Signed)**: [`dist/QuantumSafe-VPN-release.apk`](file:///D:/VPN_APP/dist/QuantumSafe-VPN-release.apk) (14.07 MB)
- **Checksums**: [`dist/SHA256SUMS.txt`](file:///D:/VPN_APP/dist/SHA256SUMS.txt)
- **Android Project Source**: [`android/`](file:///D:/VPN_APP/android/)
- **Architecture Specification**: [`ARCHITECTURE_SUMMARY.md`](file:///D:/VPN_APP/ARCHITECTURE_SUMMARY.md)
- **Test Verification Report**: [`TEST_REPORT.md`](file:///D:/VPN_APP/TEST_REPORT.md)

---

## 📱 Minimal White UI Design

The user interface follows a modern, clean, minimal white aesthetic:
- **Palette**: Pure white `#FFFFFF` background, subtle `#F8F9FA` card surfaces, `#1A1D20` charcoal text, and a restrained `#1971C2` blue accent for primary interactive actions.
- **Components**: Rounded cards, thin border strokes (`#DEE2E6`), generous whitespace, and zero decorative neon, gradients, or 3D graphics.
- **Screens**:
  1. **Home**: Primary Connect/Disconnect action button, status badge (`DISCONNECTED`, `CONNECTING`, `CONNECTED`, `ERROR`), live duration timer, and telemetry counters (bytes sent/received, packet rates).
  2. **Server Configuration**: Configurable server host/IP, port (default: 7000), timeout, and MTU with real-time input validation and Keystore-backed persistence.
  3. **Security Details**: Cryptographic suite breakdown, key length specifications, and wire protocol disclosures.
  4. **Settings & Diagnostics**: Reconnection options, live connection diagnostics log, and log export tools.

---

## 🔐 Cryptographic Wire Engine

| Layer | Algorithm / Standard | Parameters / Key Length |
| :--- | :--- | :--- |
| **Authentication** | ML-DSA-65 (NIST FIPS 204 compatible) | Public Key: 1,952 bytes; Signature: 3,309 bytes |
| **Key Encapsulation** | ML-KEM-1024 (NIST FIPS 203 compatible) | Public Key: 1,568 bytes; Ciphertext: 1,568 bytes |
| **Hash / Sponge** | Keccak-f[1600] SHA3-256 (NIST FIPS 202) | Pure-Kotlin SHA3-256 matching Python `hashlib.sha3_256` |
| **Key Derivation** | HKDF-SHA256 (RFC 5869) | 256-bit derived symmetric session key |
| **Symmetric Tunnel** | AES-256-GCM (NIST FIPS 197 AEAD) | 256-bit key, 12-byte IV, 16-byte authentication tag |
| **Replay Defense** | Monotonic Counter | 64-bit sequence counters embedded in authenticated headers |

> **Cryptographic Disclosure**: The Android client and Python server exchange authenticated packets using standard NIST wire formats (ML-DSA-65 and ML-KEM-1024 parameter sizes). The pure-Kotlin fallback engine uses deterministic seed-expansion and matrix algebra for key encapsulation. For enterprise production deployments, plug in hardware-accelerated liboqs C/JNI bindings.

---

## 🛠️ Build & Installation Guide

### Prerequisites
- Android SDK (API 26 to API 34)
- JDK 17 or JDK 21 (`JAVA_HOME` set)
- Python 3.10+ (for backend server)

### 1. Build APKs from Source
To build the application from scratch:
```powershell
# Open the android directory
cd D:\VPN_APP\android

# Build Debug APK
.\gradlew.bat assembleDebug --console=plain

# Build Signed Release APK
.\gradlew.bat assembleRelease --console=plain
```

APKs will be generated in:
- `android/app/build/outputs/apk/debug/app-debug.apk`
- `android/app/build/outputs/apk/release/app-release.apk`

And copied to `dist/`:
```powershell
.\copy_dist.ps1
```

### 2. Install on Android Phone via ADB
Connect your phone with USB debugging enabled:
```bash
adb install -r dist/QuantumSafe-VPN-release.apk
```

---

## 🖥️ Server Setup & Execution

### 1. Setup Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the VPN Server
To start the VPN server listening on port 7000:
```bash
python tunnel_server.py
```
Or use the unified runner:
```bash
python run.py
```

### 3. Linux/Cloud Deployment (IP Forwarding & NAT)
If running on a Linux VPS or dedicated gateway, enable packet forwarding so Android clients can route traffic out to the internet:
```bash
# Enable IPv4 forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Configure iptables NAT masquerade
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i tun0 -j ACCEPT
sudo iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT
```

---

## 🧪 Testing & Verification

### Run Android Unit Tests:
```powershell
cd D:\VPN_APP\android
.\gradlew.bat testDebugUnitTest
```
All 6 tests verify pure-Kotlin SHA3-256 against NIST vectors, ML-KEM key generation, ML-DSA signature verification, and AES-256-GCM AEAD framing.

### Run Python Backend Tests:
```powershell
python -m unittest discover tests
```
Runs 6/6 tests covering encryption roundtrip, key generation, framing, protocol handshake, replay protection, and Shor engine simulations.

### Verify Signatures:
```powershell
.\verify_signatures.ps1
```
Uses Android `apksigner` to verify APK Signature Scheme v2 compliance.

---

## 🔧 Troubleshooting

1. **VPN Consent Dialog on Android**:
   - The first time you tap **CONNECT**, Android will display a system security consent screen (`QuantumSafe VPN wants to set up a VPN connection`). Tap **OK** / **Accept**.
2. **Cannot Connect to Server**:
   - Verify the server IP address entered on Screen B is reachable over Wi-Fi (e.g., your laptop's LAN IP, not `127.0.0.1` or `localhost`).
   - Check firewall rules on the server machine to ensure TCP port `7000` is open.
3. **No Internet while Connected**:
   - Ensure the server host has IP forwarding enabled (`sysctl net.ipv4.ip_forward=1`) and iptables MASQUERADE configured if acting as an Internet gateway.
