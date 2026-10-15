"""
ML-DSA-65 (NIST FIPS 204) digital signatures.

Uses a real FIPS 204 implementation (dilithium-py). There is deliberately NO
fallback: the previous stand-in accepted any signature that began with the
bytes b"MLDSA65_SIG_". We fail closed instead.
"""
import os
import shutil
import time

from dilithium_py.ml_dsa import ML_DSA_65

ALGORITHM = "ML-DSA-65"

KEY_DIR = os.environ.get("VPN_KEY_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "keys"
)
PUBLIC_KEY_FILE = os.path.join(KEY_DIR, "server_mldsa65_public.key")
SECRET_KEY_FILE = os.path.join(KEY_DIR, "server_mldsa65_secret.key")

MLDSA_PUBLIC_KEY_SIZE = 1952
MLDSA_SECRET_KEY_SIZE = 4032
MLDSA_SIGNATURE_SIZE = 3309


def generate_keypair():
    """Return (public_key, secret_key)."""
    public_key, secret_key = ML_DSA_65.keygen()
    return public_key, secret_key


def sign(secret_key, message):
    if not isinstance(message, bytes):
        message = str(message).encode("utf-8")
    return ML_DSA_65.sign(secret_key, message)


def verify(public_key, message, signature):
    """Strict verification; any malformed input returns False."""
    if not isinstance(message, bytes):
        message = str(message).encode("utf-8")
    if len(public_key) != MLDSA_PUBLIC_KEY_SIZE or len(signature) != MLDSA_SIGNATURE_SIZE:
        return False
    try:
        return bool(ML_DSA_65.verify(public_key, message, signature))
    except Exception:
        return False


def _identity_is_valid(public_key, secret_key):
    """Sign/verify self-test, so stale stand-in key files are detected."""
    if len(public_key) != MLDSA_PUBLIC_KEY_SIZE or len(secret_key) != MLDSA_SECRET_KEY_SIZE:
        return False
    try:
        probe = b"identity-self-test"
        return verify(public_key, probe, sign(secret_key, probe))
    except Exception:
        return False


def load_or_create_server_identity():
    """
    Load the persistent server ML-DSA-65 identity, creating it on first run.
    Key files written by the old insecure stand-in fail the self-test; they are
    moved aside (never deleted) and a genuine identity is generated.
    """
    os.makedirs(KEY_DIR, mode=0o700, exist_ok=True)

    if os.path.exists(PUBLIC_KEY_FILE) and os.path.exists(SECRET_KEY_FILE):
        with open(PUBLIC_KEY_FILE, "rb") as f:
            public_key = f.read()
        with open(SECRET_KEY_FILE, "rb") as f:
            secret_key = f.read()
        if _identity_is_valid(public_key, secret_key):
            print("[+] Loaded existing ML-DSA-65 server identity")
            return public_key, secret_key
        stamp = time.strftime("%Y%m%d-%H%M%S")
        for path in (PUBLIC_KEY_FILE, SECRET_KEY_FILE):
            shutil.move(path, f"{path}.invalid-{stamp}")
        print("[!] Existing server key files are not a valid ML-DSA-65 identity "
              "(likely from the old stand-in). Moved aside; generating a new one.")

    print("[*] Generating new ML-DSA-65 server identity...")
    public_key, secret_key = generate_keypair()
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_key)
    fd = os.open(SECRET_KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(secret_key)
    print("[+] New ML-DSA-65 server identity created")
    return public_key, secret_key
