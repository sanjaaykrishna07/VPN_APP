# QuantumSafeVPN — Comprehensive Testing & Verification Guide

This document outlines the testing protocols for validating the Post-Quantum VPN across unit tests, local integration tests, and physical hardware over Wi-Fi.

---

## 1. Automated Test Suite

Run the full automated test suite using `run.py`:
```bash
python run.py --test
```

### Individual Unit Tests:
```bash
# 1. ML-KEM-1024 Key Encapsulation & Decapsulation
python -m tests.test_mlkem

# 2. ML-DSA-65 Digital Signature Generation & Verification
python -m tests.test_mldsa

# 3. Classical & AEAD Encryption (X25519, HKDF-SHA256, AES-256-GCM)
python -m tests.test_classical

# 4. VPN Packet Tampering & Authentication Tag Verification
python -m tests.test_vpn_tampering

# 5. Client IP Pool Allocation, Lease Management & Subnet Range
python -m tests.test_ip_pool

# 6. Full End-to-End PQC Handshake & Multi-Client Session Routing
python -m tests.test_integration
```

---

## 2. Lab Testing vs. Real Android Testing

### LAB TESTING (Local Machine / Namespaces)
- Tests cryptographic math, key exchange, encryption framing, and routing tables on loopback or network namespaces.
- Executed via `python run.py --test` and `connect_remote_device.py --server 127.0.0.1`.

### REAL ANDROID TESTING (Physical Network)
- **Topology**: Physical Android Phone $\leftrightarrow$ Wi-Fi Router $\leftrightarrow$ Linux Server $\leftrightarrow$ Internet.
- **Verification Checklist**:
  1. Phone connects to port 7000 over LAN.
  2. Handshake completes and phone displays `Connected: 10.8.0.x`.
  3. Android VpnService status bar key icon appears.
  4. Phone can resolve domain names via DNS `1.1.1.1`.
  5. Phone can browse HTTPS websites (`https://google.com`).
  6. Server shows live packet counters increasing in `/sys/class/net/tun0/statistics/rx_packets`.
