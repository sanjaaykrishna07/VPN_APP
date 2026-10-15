"""
QuantumSafeVPN protocol v2 handshake (shared by server, client and tests).

Changes from v1 (all security fixes found in the Phase 1 audit):
  * real ML-KEM-1024 / ML-DSA-65 (no hash-based stand-ins)
  * mandatory server-key pinning on the client (no trust-on-first-use by default)
  * transcript-bound, directional session keys (client->server, server->client)
  * client authentication via a per-device token, sent only inside the
    encrypted channel, checked in constant time against a salted-hash store
  * the IP lease is allocated only AFTER the client has authenticated
  * the client configuration is sent encrypted, not in clear text

Wire sequence (every item is one length-prefixed frame):
  S->C  server ML-DSA-65 public key            (1952 B)
  C->S  client ML-KEM-1024 public key          (1568 B)
  S->C  ML-KEM ciphertext                      (1568 B)
  S->C  ML-DSA signature over transcript       (3309 B)
  C->S  AES-GCM[k_c2s]( JSON{device, token} )
  S->C  AES-GCM[k_s2c]( JSON{assigned_ip,...} )
"""
import hashlib
import hmac
import json
import os
import struct
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from crypto.classical import encrypt, decrypt
from pqc.mlkem import generate_keypair, encapsulate, decapsulate, MLKEM_PUBLIC_KEY_SIZE
from pqc.mldsa import sign, verify, MLDSA_PUBLIC_KEY_SIZE

PROTOCOL_VERSION = b"QuantumSafeVPN-v2"
MAX_FRAME = 65535
AUTH_FAIL_DELAY_SEC = 0.5

MODE_STANDARD = "standard"  # X25519 + AES-256-GCM (fast, classical key exchange)
MODE_QUANTUM = "quantum"    # ML-KEM-1024 + AES-256-GCM (post-quantum key exchange)
_MODE_BYTE = {MODE_STANDARD: b"S", MODE_QUANTUM: b"Q"}
_BYTE_MODE = {v: k for k, v in _MODE_BYTE.items()}
HELLO_MAGIC = b"QSVPN2"


class HandshakeError(Exception):
    pass


class AuthenticationError(HandshakeError):
    pass


class ServerIdentityError(HandshakeError):
    pass


# ---------------------------------------------------------------- framing
def recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed by peer")
        data += chunk
    return bytes(data)


def send_frame(sock, data):
    sock.sendall(struct.pack("!I", len(data)) + data)


def recv_frame(sock):
    length = struct.unpack("!I", recv_exact(sock, 4))[0]
    if length <= 0 or length > MAX_FRAME:
        raise ValueError(f"Invalid packet length: {length}")
    return recv_exact(sock, length)


# ---------------------------------------------------------------- keys
def derive_directional_keys(shared_secret, transcript):
    """Two independent 256-bit keys, bound to the full handshake transcript."""
    okm = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=hashlib.sha256(transcript).digest(),
        info=b"QuantumSafeVPN-v2-directional-keys",
    ).derive(shared_secret)
    return okm[:32], okm[32:]  # (client->server, server->client)


def fingerprint(public_key):
    return hashlib.sha256(public_key).hexdigest()


# ---------------------------------------------------------------- client store
class ClientStore:
    """
    JSON file of per-device credentials: {device: {"salt": hex, "hash": hex}}.
    Only a salted SHA-256 of the 256-bit random token is stored, never the token.
    """

    def __init__(self, path):
        self.path = path

    def _load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _digest(salt, token):
        return hashlib.sha256(salt + token.encode("utf-8")).hexdigest()

    def add_device(self, device):
        """Create a device credential. Returns the token ONCE; it is not recoverable."""
        records = self._load()
        token = os.urandom(32).hex()
        salt = os.urandom(16)
        records[device] = {"salt": salt.hex(), "hash": self._digest(salt, token)}
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        return token

    def verify(self, device, token):
        record = self._load().get(device)
        # Compare against a dummy record when the device is unknown so that
        # timing does not reveal which device names exist.
        salt = bytes.fromhex(record["salt"]) if record else b"\x00" * 16
        expected = record["hash"] if record else "0" * 64
        actual = self._digest(salt, token if isinstance(token, str) else "")
        ok = hmac.compare_digest(actual, expected)
        return bool(record) and ok


def _raw(pub):
    return pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


# ---------------------------------------------------------------- server side
def server_handshake(sock, identity, client_store, allocate_ip, config_for_ip,
                     allowed_modes=(MODE_STANDARD, MODE_QUANTUM)):
    """
    identity:       (ml-dsa public key, ml-dsa secret key)
    allocate_ip:    callable() -> ip string or None, called only after auth
    config_for_ip:  callable(ip) -> dict sent (encrypted) to the client
    allowed_modes:  server policy; a mode not listed here is refused
    Returns (k_c2s, k_s2c, assigned_ip, device_name, mode).

    The chosen mode byte is part of the signed transcript, so a network attacker
    cannot downgrade quantum -> standard without the signature check failing.
    """
    dsa_public, dsa_secret = identity
    hello = recv_frame(sock)
    if len(hello) != len(HELLO_MAGIC) + 1 or not hello.startswith(HELLO_MAGIC):
        raise HandshakeError("Bad protocol hello")
    mode = _BYTE_MODE.get(hello[-1:])
    if mode is None or mode not in allowed_modes:
        raise HandshakeError(f"Mode not permitted by server policy: {hello[-1:]!r}")
    mbyte = _MODE_BYTE[mode]

    send_frame(sock, dsa_public)
    client_pk = recv_frame(sock)

    if mode == MODE_QUANTUM:
        if len(client_pk) != MLKEM_PUBLIC_KEY_SIZE:
            raise HandshakeError(f"Invalid ML-KEM public key size: {len(client_pk)}")
        server_part, shared_secret = encapsulate(client_pk)  # ML-KEM ciphertext
    else:
        if len(client_pk) != 32:
            raise HandshakeError(f"Invalid X25519 public key size: {len(client_pk)}")
        eph = X25519PrivateKey.generate()
        server_part = _raw(eph.public_key())  # server X25519 public value
        shared_secret = eph.exchange(X25519PublicKey.from_public_bytes(client_pk))

    transcript = PROTOCOL_VERSION + mbyte + client_pk + server_part
    send_frame(sock, server_part)
    send_frame(sock, sign(dsa_secret, transcript))

    k_c2s, k_s2c = derive_directional_keys(shared_secret, transcript)

    # Client must prove it is an enrolled device before it is given any lease.
    try:
        auth = json.loads(decrypt(k_c2s, recv_frame(sock)).decode("utf-8"))
        device, token = str(auth.get("device", "")), auth.get("token", "")
    except Exception:
        time.sleep(AUTH_FAIL_DELAY_SEC)
        raise AuthenticationError("Malformed or undecryptable authentication frame")
    if not client_store.verify(device, token):
        time.sleep(AUTH_FAIL_DELAY_SEC)
        raise AuthenticationError("Client authentication failed")

    assigned_ip = allocate_ip()
    if not assigned_ip:
        raise HandshakeError("No available IP addresses in VPN pool")
    send_frame(sock, encrypt(k_s2c, json.dumps(config_for_ip(assigned_ip)).encode("utf-8")))
    return k_c2s, k_s2c, assigned_ip, device, mode


# ---------------------------------------------------------------- client side
def client_handshake(sock, pinned_server_key, device, token, mode=MODE_QUANTUM):
    """
    pinned_server_key: the server's ML-DSA-65 public key bytes (REQUIRED).
    mode: MODE_STANDARD or MODE_QUANTUM (this is the app's quantum-safe toggle).
    Returns (k_c2s, k_s2c, config_dict). Raises ServerIdentityError on mismatch.
    """
    if mode not in _MODE_BYTE:
        raise ValueError(f"Unknown mode: {mode}")
    if not pinned_server_key:
        raise ServerIdentityError("A pinned server key is required (no trust-on-first-use)")
    mbyte = _MODE_BYTE[mode]

    send_frame(sock, HELLO_MAGIC + mbyte)
    server_pk = recv_frame(sock)
    if len(server_pk) != MLDSA_PUBLIC_KEY_SIZE or not hmac.compare_digest(server_pk, pinned_server_key):
        raise ServerIdentityError(
            f"Server key does not match pin (got {fingerprint(server_pk)[:16]}..., "
            f"expected {fingerprint(pinned_server_key)[:16]}...)"
        )

    if mode == MODE_QUANTUM:
        client_pk, kem_sk = generate_keypair()
    else:
        eph = X25519PrivateKey.generate()
        client_pk = _raw(eph.public_key())
    send_frame(sock, client_pk)

    server_part = recv_frame(sock)
    signature = recv_frame(sock)
    transcript = PROTOCOL_VERSION + mbyte + client_pk + server_part
    if not verify(server_pk, transcript, signature):
        raise ServerIdentityError("ML-DSA-65 signature verification failed (possible downgrade or MITM)")

    if mode == MODE_QUANTUM:
        shared_secret = decapsulate(kem_sk, server_part)
    else:
        if len(server_part) != 32:
            raise HandshakeError("Invalid X25519 server public value")
        shared_secret = eph.exchange(X25519PublicKey.from_public_bytes(server_part))
    k_c2s, k_s2c = derive_directional_keys(shared_secret, transcript)

    send_frame(sock, encrypt(k_c2s, json.dumps({"device": device, "token": token}).encode("utf-8")))
    try:
        config = json.loads(decrypt(k_s2c, recv_frame(sock)).decode("utf-8"))
    except (ConnectionError, ValueError) as exc:
        raise AuthenticationError(f"Server rejected authentication or closed the connection: {exc}")
    return k_c2s, k_s2c, config
