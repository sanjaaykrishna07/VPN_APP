# QuantumSafeVPN — Security Analysis & Threat Model

This document details the security posture, cryptographic guarantees, and mitigation strategies implemented in QuantumSafeVPN.

---

## 1. Threat Model & Security Properties

### Post-Quantum Security (NIST Level 5)
- **Harvest-Now-Decrypt-Later (HNDL) Defense**: An adversary recording encrypted VPN traffic cannot decrypt historical sessions in the quantum era because session keys are established using **ML-KEM-1024** (FIPS 203).
- **Quantum-Resistant Identity Authentication**: Server impersonation and Man-in-the-Middle (MITM) attacks are thwarted via **ML-DSA-65** (FIPS 204) lattice-based digital signatures pinned by public key fingerprint.

### Authenticated Encryption & Integrity
- **AES-256-GCM** (NIST FIPS 197) guarantees both confidentiality and authenticity.
- Any modification of ciphertext or nonce during transit triggers an authentication tag mismatch, causing the receiver to discard the packet immediately.

### Replay Attack Prevention
- A 64-bit monotonically increasing sequence number is embedded within the authenticated payload of every packet.
- The receiver enforces strict monotonic sequence checks, dropping duplicate, delayed, or out-of-window replayed packets.

### Nonce Uniqueness
- Every frame utilizes a freshly generated 12-byte cryptographically secure pseudorandom nonce (`os.urandom(12)` / `SecureRandom`), preventing AES-GCM nonce reuse vulnerabilities.

### Secret Isolation & No Plaintext Logging
- Private keys (`server_mldsa65_secret.key`) are stored with strict file permissions (`0600`).
- Handshake session keys and raw plaintext user traffic are strictly excluded from all application log streams.
