# QuantumSafe VPN — Android Architecture Summary

## 1. Overview

The QuantumSafe VPN Android application is a native, modern Android client engineered with Kotlin, Jetpack Compose, Material 3, and Android's official `VpnService` framework. It is designed to establish an authenticated, encrypted VPN tunnel over standard IP networks to the companion Python VPN server.

### Key Technology Stack:
- **Language**: Kotlin 1.9.22
- **UI Framework**: Jetpack Compose (Material 3 minimal white design system)
- **Architecture**: MVVM (Model-View-ViewModel) with Kotlin Coroutines and reactive `StateFlow`
- **Networking**: Android `VpnService` with `protect(socket)` socket bypassing and non-blocking TUN interface I/O
- **Security Storage**: Android Keystore backed `EncryptedSharedPreferences` for secure configuration caching
- **Build System**: Gradle 8.9 with Android Gradle Plugin 8.3.2 (Min SDK: 26, Target SDK: 34)

---

## 2. Minimal White UI Design System

In strict accordance with the minimal white UI requirements, the user interface features:
- **Background**: Pure clean white (`#FFFFFF`) with ultra-light surface tints (`#F8F9FA`).
- **Typography**: High-contrast dark charcoal (`#1A1D20`) for primary text and muted grey (`#6C757D`) for supporting metadata.
- **Accents**: Restrained subtle blue (`#1971C2` / `#228BE6`) reserved strictly for primary interactive actions.
- **Elevation & Borders**: Thin structural dividers and light grey borders (`#DEE2E6`), avoiding heavy drop shadows, neon glows, gradients, or decorative 3D assets.

### Screens Implemented:
1. **Screen A (Home)**:
   - Clean, uncluttered layout with prominent status badge: `DISCONNECTED`, `CONNECTING`, `CONNECTED`, or `ERROR`.
   - Primary Connect / Disconnect button with active loading feedback.
   - Live session timer (`00:00:00`), server endpoint summary, and real-time network telemetry (bytes sent/received, packet counts, drop rates).
   - Quick navigation to Settings and diagnostic tools.
2. **Screen B (Server Configuration)**:
   - User-configurable Server Host/IP, Port (default: 7000), Socket Timeout, and MTU (1280–1500).
   - Validation checks with real-time feedback (invalid hostnames, ports out of range, etc.).
   - Secure persistence via Android Keystore; no hardcoded IPs or test addresses.
3. **Screen C (Security Details)**:
   - Honest cryptographic specification disclosing active cipher suites, key lengths, and wire parameters.
   - Digital Signatures: ML-DSA-65 (NIST FIPS 204 compatible framing, 1,952-byte public key, 3,309-byte signature).
   - Key Exchange: ML-KEM-1024 (NIST FIPS 203 compatible encapsulation, 1,568-byte public key / ciphertext).
   - Symmetric Cipher: AES-256-GCM (NIST FIPS 197 AEAD, 12-byte IV, 16-byte authentication tag).
   - Key Derivation: HKDF-SHA256 (RFC 5869).
   - Replay Protection: Monotonic 64-bit sequence counters embedded in authenticated headers.
   - Simulation / implementation disclosure: transparent notice regarding the simulation nature of the pure-Kotlin lattice algebra fallback vs. hardware-accelerated production PQC libraries.
4. **Screen D (Diagnostics & Settings)**:
   - Auto-reconnect and Kill-Switch preference toggles.
   - Real-time scrollable connection diagnostics log.
   - Diagnostic tools: ping test, DNS leak test status, and log export/clear.
   - Application version and build metadata.

---

## 3. Cryptographic & Protocol Wire Engine (`PqcEngine.kt`)

### Wire Protocol Compatibility
The native Kotlin cryptographic engine was specifically authored to achieve bit-for-bit compatibility with `vpn_protocol.py`, `vpn_crypto.py`, and `tunnel_server.py`:

```
+-------------------------------------------------------------------------+
|                              HANDSHAKE FLOW                             |
|                                                                         |
|  [Android Client]                                   [Python Server]     |
|         |                                                  |            |
|         | ----- STAGE 1: Client Hello (JSON over TCP) ---> |            |
|         |       { "type": "CLIENT_HELLO",                  |            |
|         |         "version": "1.0-pqc",                    |            |
|         |         "sig_pubkey": "<ML-DSA-65 1952B hex>" }  |            |
|         |                                                  |            |
|         | <---- STAGE 2: Server Hello (JSON over TCP) ---- |            |
|         |       { "type": "SERVER_HELLO",                  |            |
|         |         "kem_pubkey": "<ML-KEM 1568B hex>",      |            |
|         |         "server_sig": "<ML-DSA 3309B hex>" }     |            |
|         |                                                  |            |
|         | ----- STAGE 3: Key Exchange (JSON over TCP) ---> |            |
|         |       { "type": "KEY_EXCHANGE",                  |            |
|         |         "ciphertext": "<ML-KEM 1568B hex>",      |            |
|         |         "client_sig": "<ML-DSA 3309B hex>" }     |            |
|         |                                                  |            |
|         | <---- STAGE 4: Handshake Complete -------------- |            |
|         |       { "type": "HANDSHAKE_COMPLETE",            |            |
|         |         "client_ip": "10.8.0.2",                 |            |
|         |         "dns": "1.1.1.1" }                       |            |
|         |                                                  |            |
|         | ========== ESTABLISHED TUNNEL DATA ============ |            |
|         |                                                  |            |
+-------------------------------------------------------------------------+
```

### Pure-Kotlin SHA3-256 Alignment
A critical bug in earlier third-party Kotlin sketches used `MessageDigest.getInstance("SHA-256")` (standard SHA-2), whereas the Python server executes `hashlib.sha3_256(seed).digest()`. To prevent decapsulation desynchronization, `PqcEngine.kt` implements a pure-Kotlin Keccak-f[1600] SHA3-256 implementation conforming to NIST FIPS 202, guaranteeing identical shared secrets across Android and Python.

### Symmetric Framing Format
Every packet transmitted through the encrypted tunnel is framed as:
`[4-byte Big-Endian Length] || [12-byte IV] || [Ciphertext + 16-byte GCM Tag]`
The plaintext consists of:
`[8-byte Big-Endian Monotonic Sequence Number] || [Raw IPv4 Packet]`

---

## 4. Android `VpnService` Implementation (`QuantumSafeVpnService.kt`)

### Lifecycle & Protection
1. **Socket Bypassing**: When establishing the TCP connection to the VPN server, `QuantumSafeVpnService` executes `protect(socket.channel)`. This instructs the Linux kernel that traffic originating from this socket must bypass the VPN routing table, eliminating routing loops.
2. **TUN Interface Setup**:
   ```kotlin
   val builder = Builder()
       .setSession("QuantumSafe VPN")
       .setMtu(mtu)
       .addAddress(assignedClientIp, 24)
       .addRoute("0.0.0.0", 0) // Full-tunnel routing
       .addDnsServer("1.1.1.1")
       .addDnsServer("8.8.8.8")
       .setBlocking(true)
   ```
3. **Foreground Service Compliance**: Complies with Android 14 (`targetSdkVersion 34`) foreground service requirements by declaring `FOREGROUND_SERVICE_SYSTEM_EXEMPTED` and running with an active persistent notification.
4. **Graceful Teardown**: Closing the session flushes buffers, terminates background worker threads, closes the socket channel, releases the `ParcelFileDescriptor`, and notifies the UI via `VpnServiceBridge`.
