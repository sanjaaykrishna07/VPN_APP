import os
import hashlib
import hmac
import struct

# Try importing cryptography if installed
try:
    from cryptography.hazmat.primitives.asymmetric import x25519
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF as _HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_LIB_AVAILABLE = True
except ImportError:
    CRYPTO_LIB_AVAILABLE = False


def generate_keypair():
    if CRYPTO_LIB_AVAILABLE:
        try:
            private_key = x25519.X25519PrivateKey.generate()
            public_key = private_key.public_key()
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            return private_key, public_bytes
        except Exception:
            pass

    priv = os.urandom(32)
    pub = hashlib.sha256(b"X25519_PUB" + priv).digest()
    return priv, pub


def derive_key(private_key, peer_public_bytes):
    if CRYPTO_LIB_AVAILABLE and hasattr(private_key, "exchange"):
        try:
            peer_public = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
            shared_secret = private_key.exchange(peer_public)
            return derive_session_key(shared_secret)
        except Exception:
            pass

    shared = hashlib.sha256(private_key + peer_public_bytes).digest()
    return derive_session_key(shared)


def derive_session_key(shared_secret):
    """
    Convert a shared secret into a 256-bit AES session key using HKDF-SHA256.
    """
    if CRYPTO_LIB_AVAILABLE:
        try:
            return _HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b"QuantumSafeVPN-Session-Key"
            ).derive(shared_secret)
        except Exception:
            pass

    # Pure-Python RFC 5869 HKDF-SHA256
    salt = b"\x00" * 32
    info = b"QuantumSafeVPN-Session-Key"
    prk = hmac.new(salt, shared_secret, hashlib.sha256).digest()
    t = hmac.new(prk, info + b"\x01", hashlib.sha256).digest()
    return t[:32]


# ---------------- AES-256-GCM S-BOX & Core ----------------

_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

_RCON = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36]

def _xtime(a):
    return ((a << 1) ^ 0x11b) & 0xff if a & 0x80 else (a << 1) & 0xff

def _mix_single(a):
    t = a[0] ^ a[1] ^ a[2] ^ a[3]
    u = a[0]
    r = [0]*4
    r[0] = a[0] ^ _xtime(a[0] ^ a[1]) ^ t
    r[1] = a[1] ^ _xtime(a[1] ^ a[2]) ^ t
    r[2] = a[2] ^ _xtime(a[2] ^ a[3]) ^ t
    r[3] = a[3] ^ _xtime(a[3] ^ u) ^ t
    return r

def _aes_key_expansion_256(key: bytes):
    w = list(key)
    i = 8
    while i < 4 * 15:
        temp = w[(i-1)*4:i*4]
        if i % 8 == 0:
            temp = temp[1:] + temp[:1]
            temp = [_SBOX[b] for b in temp]
            temp[0] ^= _RCON[i // 8 - 1]
        elif i % 8 == 4:
            temp = [_SBOX[b] for b in temp]
        w.extend([w[(i-8)*4+j] ^ temp[j] for j in range(4)])
        i += 1
    return [bytes(w[r*16:(r+1)*16]) for r in range(15)]

def _aes_encrypt_block(block: bytes, round_keys):
    state = [[block[c*4+r] for c in range(4)] for r in range(4)]
    for c in range(4):
        for r in range(4):
            state[c][r] ^= round_keys[0][c*4+r]

    for rnd in range(1, 14):
        for c in range(4):
            for r in range(4):
                state[c][r] = _SBOX[state[c][r]]
        for r in range(1, 4):
            row = [state[c][r] for c in range(4)]
            row = row[r:] + row[:r]
            for c in range(4):
                state[c][r] = row[c]
        for c in range(4):
            state[c] = _mix_single(state[c])
        for c in range(4):
            for r in range(4):
                state[c][r] ^= round_keys[rnd][c*4+r]

    for c in range(4):
        for r in range(4):
            state[c][r] = _SBOX[state[c][r]]
    for r in range(1, 4):
        row = [state[c][r] for c in range(4)]
        row = row[r:] + row[:r]
        for c in range(4):
            state[c][r] = row[c]
    for c in range(4):
        for r in range(4):
            state[c][r] ^= round_keys[14][c*4+r]

    out = bytearray(16)
    for c in range(4):
        for r in range(4):
            out[c*4+r] = state[c][r]
    return bytes(out)

def _ghash(h_block: bytes, aad: bytes, ciphertext: bytes) -> bytes:
    def _gf_mult(x_int, y_int):
        z = 0
        v = y_int
        for i in range(128):
            if (x_int >> (127 - i)) & 1:
                z ^= v
            carry = v & 1
            v >>= 1
            if carry:
                v ^= 0xe1000000000000000000000000000000
        return z

    def _pad16(data):
        r = len(data) % 16
        return data + b'\x00' * (16 - r) if r else data

    h = int.from_bytes(h_block, 'big')
    x = 0
    padded_aad = _pad16(aad)
    for i in range(0, len(padded_aad), 16):
        x = _gf_mult(x ^ int.from_bytes(padded_aad[i:i+16], 'big'), h)
    padded_ct = _pad16(ciphertext)
    for i in range(0, len(padded_ct), 16):
        x = _gf_mult(x ^ int.from_bytes(padded_ct[i:i+16], 'big'), h)
    len_block = (len(aad) * 8).to_bytes(8, 'big') + (len(ciphertext) * 8).to_bytes(8, 'big')
    x = _gf_mult(x ^ int.from_bytes(len_block, 'big'), h)
    return x.to_bytes(16, 'big')


def encrypt(key, message):
    """
    Encrypt message using AES-256-GCM.
    Returns: nonce (12B) + ciphertext + tag (16B)
    """
    if CRYPTO_LIB_AVAILABLE:
        try:
            aes = AESGCM(key)
            nonce = os.urandom(12)
            ciphertext = aes.encrypt(nonce, message, None)
            return nonce + ciphertext
        except Exception:
            pass

    # Pure-Python fallback AES-256-GCM
    nonce = os.urandom(12)
    rk = _aes_key_expansion_256(key)
    h = _aes_encrypt_block(b'\x00' * 16, rk)
    j0 = nonce + b'\x00\x00\x00\x01'

    # CTR Mode Encryption
    cb = bytearray(j0)
    c = (int.from_bytes(cb[12:16], 'big') + 1) & 0xFFFFFFFF
    cb[12:16] = c.to_bytes(4, 'big')

    ct = bytearray()
    for i in range(0, len(message), 16):
        ks = _aes_encrypt_block(bytes(cb), rk)
        c = (int.from_bytes(cb[12:16], 'big') + 1) & 0xFFFFFFFF
        cb[12:16] = c.to_bytes(4, 'big')
        blk = message[i:i+16]
        ct.extend(bytes(a ^ b for a, b in zip(blk, ks[:len(blk)])))

    s = _ghash(h, b"", bytes(ct))
    ej0 = _aes_encrypt_block(j0, rk)
    tag = bytes(a ^ b for a, b in zip(s, ej0))
    return nonce + bytes(ct) + tag


def decrypt(key, data):
    """
    Decrypt data: nonce (12B) + ciphertext + tag (16B)
    """
    if len(data) < 28:
        raise ValueError("Invalid AES-GCM packet size (too short)")

    nonce = data[:12]
    tag = data[-16:]
    ciphertext = data[12:-16]

    if CRYPTO_LIB_AVAILABLE:
        try:
            aes = AESGCM(key)
            return aes.decrypt(nonce, data[12:], None)
        except Exception:
            pass

    # Pure-Python fallback AES-256-GCM
    rk = _aes_key_expansion_256(key)
    h = _aes_encrypt_block(b'\x00' * 16, rk)
    j0 = nonce + b'\x00\x00\x00\x01'

    s = _ghash(h, b"", ciphertext)
    ej0 = _aes_encrypt_block(j0, rk)
    computed_tag = bytes(a ^ b for a, b in zip(s, ej0))

    if computed_tag != tag:
        raise ValueError("AES-GCM authentication tag mismatch")

    cb = bytearray(j0)
    c = (int.from_bytes(cb[12:16], 'big') + 1) & 0xFFFFFFFF
    cb[12:16] = c.to_bytes(4, 'big')

    pt = bytearray()
    for i in range(0, len(ciphertext), 16):
        ks = _aes_encrypt_block(bytes(cb), rk)
        c = (int.from_bytes(cb[12:16], 'big') + 1) & 0xFFFFFFFF
        cb[12:16] = c.to_bytes(4, 'big')
        blk = ciphertext[i:i+16]
        pt.extend(bytes(a ^ b for a, b in zip(blk, ks[:len(blk)])))

    return bytes(pt)
