# QuantumSafeVPN — Technical Architecture & Audit Report

## 1. System Overview

QuantumSafeVPN is a genuine post-quantum virtual private network engineered to tunnel raw IP packets between an Android device (or remote client) and a Linux/Kali server.

```
+-------------------------------------------------------------------------+
|                         PHYSICAL ANDROID PHONE                          |
|                                                                         |
|  [Android Applications] (Web Browser, Applications, DNS queries)        |
|            |                                                            |
|            v (Raw IPv4 Packets)                                         |
|  [Android VpnService / TUN Interface] (10.8.0.x/24, Route: 0.0.0.0/0)   |
|            |                                                            |
|            v (FileInputStream read)                                     |
|  [Kotlin PqcEngine]                                                     |
|      - Encrypt: AES-256-GCM (256-bit Key, 12B Nonce, 16B Tag)           |
|      - Frame: [Length: 4B] + [Nonce: 12B] + [Seq: 8B + Ciphertext] + [Tag: 16B]
|            |                                                            |
|            v (Protected TCP Socket - Bypass VPN Loop)                   |
+-------------------------------------------------------------------------+
             |
             | Wi-Fi LAN / TCP Stream (Port 7000)
             v
+-------------------------------------------------------------------------+
|                        LINUX / KALI VPN SERVER                          |
|                                                                         |
|  [vpn/tunnel_server.py] (Listening on 0.0.0.0:7000)                     |
|      - Authenticate Server Identity: ML-DSA-65 (NIST FIPS 204)          |
|      - Key Encapsulation: ML-KEM-1024 (NIST FIPS 203)                   |
|      - Key Derivation: HKDF-SHA256 (RFC 5869)                           |
|      - Dynamic IP Lease: vpn/ip_pool.py (10.8.0.2 - 10.8.0.254)         |
|      - Anti-Replay: 64-bit Monotonic Sequence Counter Verification      |
|            |                                                            |
|            v (Decrypted IPv4 Packets written to TUN)                    |
|  [Linux Kernel TUN Interface] (tun0: 10.8.0.1/24)                       |
|            |                                                            |
|            v (net.ipv4.ip_forward = 1)                                  |
|  [Linux Kernel NAT Engine] (iptables POSTROUTING MASQUERADE)            |
|            |                                                            |
|            v (Outbound to physical WAN: eth0 / wlan0)                   |
+-------------------------------------------------------------------------+
             |
             v
   [Public Internet] (Websites, Cloud Endpoints, External DNS 1.1.1.1)
```

---

## 2. Component Implementation Analysis

| Component | Architecture Role | Verification Status | Implementation Notes |
| :--- | :--- | :--- | :--- |
| **Android VpnService** | Intercepts all device IP packets | **Implemented** | Configured in `QuantumSafeVpnService.kt` with `protect(socket)` to avoid recursive routing loops. |
| **PQC Key Exchange** | Establishes shared secret against quantum adversaries | **Verified** | Implemented with ML-KEM-1024 (FIPS 203). Tested in `test_mlkem.py`. |
| **PQC Authentication** | Verifies server identity with zero classical dependencies | **Verified** | Implemented with ML-DSA-65 (FIPS 204). Tested in `test_mldsa.py`. |
| **Session Key Derivation** | Expands shared secret into 256-bit AES key | **Verified** | RFC 5869 HKDF-SHA256 with domain separation `QuantumSafeVPN-Session-Key`. |
| **Packet Encryption** | Encrypts raw IP packets at line-rate | **Verified** | Authenticated AES-256-GCM with fresh 12B nonces and 16B tags. Tested in `test_vpn_tampering.py`. |
| **Anti-Replay Defense** | Rejects duplicated or re-ordered packets | **Verified** | 64-bit sequence counters embedded in authenticated payload. |
| **Dynamic IP Pool** | Allocates non-colliding VPN IPs | **Verified** | Thread-safe lease allocation (`10.8.0.2` - `10.8.0.254`) in `vpn/ip_pool.py`. |
| **Linux TUN Forwarder** | Reads return traffic and dispatches by destination IP | **Verified** | Multi-client dispatch loop in `vpn/tunnel_server.py`. |
| **Linux IP Forwarding & NAT** | Routes decrypted VPN packets to WAN interface | **Verified** | Automated in `vpn/nat_manager.py` and `scripts/setup_network.sh`. |

---

## 3. Wire Protocol & Serialization

### Handshake Sequence:
1. **Server Hello**: Server sends `ML-DSA-65 Public Key (1952 Bytes)`.
2. **Client Key Exchange**: Client transmits `ML-KEM-1024 Ephemeral Public Key (1568 Bytes)`.
3. **Server Response**:
   - Frame 1: `ML-KEM-1024 Ciphertext (1568 Bytes)`
   - Frame 2: `ML-DSA-65 Signature (3309 Bytes)` over transcript `b"QuantumSafeVPN-v1" + client_kem_pk + ciphertext`
   - Frame 3: `Configuration JSON` containing assigned IP, subnet, DNS servers (`1.1.1.1, 8.8.8.8`), and MTU (`1400`).
4. **Key Derivation**: Both endpoints compute session key:
   $$\text{Key} = \text{HKDF-SHA256}(\text{shared\_secret}, \text{salt}=0^{32}, \text{info}=\text{"QuantumSafeVPN-Session-Key"})$$
