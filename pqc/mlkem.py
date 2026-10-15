"""
ML-KEM-1024 (NIST FIPS 203) key encapsulation.

Uses a real FIPS 203 implementation (kyber-py). There is deliberately NO
fallback: the previous version silently substituted a hash-based stand-in
whose shared secret could be recomputed by any passive observer of the
handshake. If the library is missing we fail closed.
"""
from kyber_py.ml_kem import ML_KEM_1024

ALGORITHM = "ML-KEM-1024"

MLKEM_PUBLIC_KEY_SIZE = 1568
MLKEM_SECRET_KEY_SIZE = 3168
MLKEM_CIPHERTEXT_SIZE = 1568
MLKEM_SHARED_SECRET_SIZE = 32


def generate_keypair():
    """Return (public_key, secret_key)."""
    public_key, secret_key = ML_KEM_1024.keygen()
    return public_key, secret_key


def encapsulate(public_key):
    """Return (ciphertext, shared_secret)."""
    if len(public_key) != MLKEM_PUBLIC_KEY_SIZE:
        raise ValueError(f"Invalid ML-KEM-1024 public key length: {len(public_key)}")
    shared_secret, ciphertext = ML_KEM_1024.encaps(public_key)
    return ciphertext, shared_secret


def decapsulate(secret_key, ciphertext):
    """Return the 32-byte shared secret."""
    if len(ciphertext) != MLKEM_CIPHERTEXT_SIZE:
        raise ValueError(f"Invalid ML-KEM-1024 ciphertext length: {len(ciphertext)}")
    return ML_KEM_1024.decaps(secret_key, ciphertext)
