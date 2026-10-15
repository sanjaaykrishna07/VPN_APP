# QuantumSafeVPN — System Architecture & Wire Protocol Specification

## 1. Wire Protocol Specification

The wire protocol operates over TCP (default port `7000`). All messages follow length-prefixed framing.

### Framing Format
Each frame is prefixed with a 4-byte big-endian unsigned 32-bit integer representing the payload length:
```
+--------------------------+---------------------------------------------+
| Length (4 Bytes uint32)  |               Payload (N Bytes)             |
+--------------------------+---------------------------------------------+
```

---

## 2. 4-Stage Post-Quantum Handshake

```
Client                                                   Server
  |                                                         |
  | <----------------- Stage 1: Server Identity ----------- |
  |     ML-DSA-65 Public Key (1952 Bytes)                   |
  |                                                         |
  | [Verify Pinned SHA-256 Identity]                        |
  | [Generate Ephemeral ML-KEM-1024 Keypair]                |
  |                                                         |
  | ----------------- Stage 2: Ephemeral KEM -------------> |
  |     ML-KEM-1024 Public Key (1568 Bytes)                 |
  |                                                         |
  |                                                         | [Encapsulate Shared Secret]
  |                                                         | [Sign Transcript with ML-DSA]
  |                                                         | [Allocate Dynamic Client IP]
  |                                                         |
  | <---------------- Stage 3: Ciphertext & Config -------- |
  |     Frame A: ML-KEM-1024 Ciphertext (1568 Bytes)        |
  |     Frame B: ML-DSA-65 Signature (3309 Bytes)           |
  |     Frame C: Config JSON (Assigned IP, DNS, MTU)        |
  |                                                         |
  | [Verify ML-DSA-65 Signature over Transcript]            |
  | [Decapsulate ML-KEM-1024 Shared Secret]                 |
  |                                                         |
  | ============== Stage 4: Key Derivation ================ |
  |   Session Key = HKDF-SHA256(shared_secret,              |
  |                            salt=0x00*32,                |
  |                            info="QuantumSafeVPN-Session-Key")
  |                                                         |
  | [Establish TUN: 10.8.0.x/24]   [Register Client Route]  |
```

### Transcript Definition for ML-DSA-65 Signature:
$$\text{Transcript} = \text{"QuantumSafeVPN-v1"} \parallel \text{Client\_KEM\_PK} \parallel \text{KEM\_Ciphertext}$$

---

## 3. Data Transmission Framing

Once the session key is established, all raw IP packets passing through the TUN device are framed as follows:

```
+---------------+----------------+-----------------------+-------------------+
| Length (4B)   | Nonce (12B)    | Ciphertext (N+8 Bytes)| Auth Tag (16B)    |
+---------------+----------------+-----------------------+-------------------+
                                   |
         Plaintext before AES-GCM: [Sequence (8B uint64)] + [Raw IP Packet (N Bytes)]
```

### Anti-Replay Mechanism:
1. Every transmitted packet increments an 8-byte unsigned 64-bit integer sequence counter (`send_seq`).
2. The receiver validates that `received_seq > last_seen_seq`.
3. If an adversary replays an encrypted frame, it is immediately discarded upon sequence inspection.
