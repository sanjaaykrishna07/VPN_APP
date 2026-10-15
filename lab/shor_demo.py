"""
QuantumSafe VPN - Shor's-algorithm laboratory (ISOLATED from the production VPN).

Everything here uses SYNTHETIC traffic between local objects. Nothing touches a
network, the real server, or real user data.

STANDARD mode (toy "16-bit VPN"): the session key is wrapped with a 16-bit RSA
    modulus. An attacker who recorded the handshake factors N with Shor's
    algorithm, rebuilds the private key, unwraps the session key and reads the
    traffic.
QUANTUM-SAFE mode: the session key comes from ML-KEM-1024 (lattice based). There
    is no integer modulus and no hidden period for Shor's algorithm to find, so
    the same attack has nothing to work on.

Honest scope notes
  * Shor's algorithm breaks public-key exchange (RSA / DH / ECC). It does not
    attack AES. A 16-bit *symmetric* key would just be brute-forced. The 16 bits
    here are the RSA modulus; the traffic key is a real 128-bit AES-GCM key that
    is exposed only because the key exchange falls.
  * No quantum computer today can run Shor on real key sizes. The quantum
    subroutine (order finding) is EMULATED: the emulator knows the true order r
    and draws the measurement from the exact distribution a quantum computer
    would give. tests/test_lab_shor.py checks that distribution against an exact
    state-vector (FFT) simulation. Everything after the measurement (continued
    fractions, gcd, key recovery) is the real classical part of Shor.
  * "Quantum-safe" means no known quantum attack, not a mathematical proof.

Run:  python lab/shor_demo.py --mode both
"""
import argparse
import math
import os
import random
import sys
import time
from fractions import Fraction

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.exceptions import InvalidTag  # noqa: E402
from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402
from cryptography.hazmat.primitives.kdf.hkdf import HKDF  # noqa: E402

from pqc import mlkem  # noqa: E402

# Synthetic "user" traffic. Fake data only.
SYNTHETIC_TRAFFIC = [
    b"GET /login HTTP/1.1  Host: demo-bank.example",
    b"POST /login  user=demo_user&password=DEMO-ONLY-NOT-REAL",
    b"GET /account/balance  (synthetic) balance=1234.56",
    b"search?q=synthetic+test+query",
]


# ============================================================= toy 16-bit RSA
def _is_prime(n):
    if n < 2:
        return False
    return all(n % i for i in range(2, int(n ** 0.5) + 1))


def generate_rsa16(rng):
    """Toy RSA with a 16-bit modulus (32768 <= N < 65536). Educational only."""
    primes = [p for p in range(100, 256) if _is_prime(p)]
    while True:
        p, q = rng.sample(primes, 2)
        n = p * q
        if not 32768 <= n < 65536:
            continue
        phi = (p - 1) * (q - 1)
        for e in (17, 5, 7, 3, 11, 13):
            if math.gcd(e, phi) == 1:
                return {"n": n, "e": e, "d": pow(e, -1, phi), "p": p, "q": q}


def rsa_wrap_key(key_bytes, n, e):
    """Wrap each key byte separately (each byte < 256 < N)."""
    return [pow(b, e, n) for b in key_bytes]


def rsa_unwrap_key(cipher_ints, n, d):
    return bytes(pow(c, d, n) for c in cipher_ints)


# ============================================================ Shor's algorithm
def true_order(a, n):
    """Classical stand-in used ONLY inside the emulated quantum subroutine."""
    r, x = 1, a % n
    while x != 1:
        x = (x * a) % n
        r += 1
    return r


def _sample(probs, rng):
    u = rng.random()
    return int(min(np.searchsorted(np.cumsum(probs), u), len(probs) - 1))


def emulate_quantum_order_finding(a, n, rng, counting_bits=None):
    """
    Emulates the measurement of Shor's order-finding circuit.

    Counting register of t qubits in uniform superposition -> |x>|a^x mod N>
    -> measure work register -> counting register is a comb over x = x0 + j*r
    -> QFT -> measure. The QFT amplitude is a Dirichlet kernel peaked at
    multiples of Q/r; we sample the outcome from that exact distribution.
    Returns (k, Q).
    """
    t = counting_bits or 2 * n.bit_length()
    q = 1 << t
    r = true_order(a, n)
    x0 = rng.randrange(r)
    m = (q - x0 + r - 1) // r
    c = rng.randrange(r)
    k0 = round(c * q / r)
    window = np.arange(max(0, k0 - 64), min(q, k0 + 65), dtype=np.int64)
    theta = np.pi * r * window / q
    s = np.sin(theta)
    safe = np.where(np.abs(s) < 1e-12, 1.0, s)
    probs = np.where(np.abs(s) < 1e-12, float(m) ** 2, (np.sin(m * theta) / safe) ** 2)
    probs = probs / probs.sum()
    return int(window[_sample(probs, rng)]), q


def exact_order_distribution(a, n, t):
    """Exact state-vector simulation of the same circuit (small n only)."""
    q = 1 << t
    vals = np.empty(q, dtype=np.int64)
    cur = 1
    for i in range(q):
        vals[i] = cur
        cur = (cur * a) % n
    probs = np.zeros(q)
    ys = np.unique(vals)
    for y in ys:
        comb = (vals == y).astype(np.complex128)
        comb /= np.sqrt(comb.sum().real)
        amp = np.fft.fft(comb) / np.sqrt(q)
        probs += np.abs(amp) ** 2 / len(ys)
    return probs


def recover_order(k, q, a, n):
    """Continued-fraction post-processing; also tries small multiples."""
    if k == 0:
        return None
    r0 = Fraction(k, q).limit_denominator(n).denominator
    for mult in range(1, 7):
        r = r0 * mult
        if r < n and pow(a, r, n) == 1:
            return r
    return None


def shor_factor(n, rng=None, max_attempts=200, log=print):
    """Factor an odd composite n. Returns (p, q, attempts)."""
    rng = rng or random.Random()
    if n % 2 == 0:
        return 2, n // 2, 0
    for attempt in range(1, max_attempts + 1):
        a = rng.randrange(2, n - 1)
        g = math.gcd(a, n)
        if g > 1:
            log(f"    attempt {attempt}: a={a} shares factor {g} (lucky, no quantum step needed)")
            return g, n // g, attempt
        k, q = emulate_quantum_order_finding(a, n, rng)
        r = recover_order(k, q, a, n)
        log(f"    attempt {attempt}: a={a}  measured k={k}/{q}  -> order r={r}")
        if r is None or r % 2:
            continue
        half = pow(a, r // 2, n)
        if half == n - 1:
            continue
        p = math.gcd(half - 1, n)
        if 1 < p < n:
            return p, n // p, attempt
    raise RuntimeError("Shor did not find a factor within the attempt limit")


# ============================================================== the two modes
def _aes_traffic(key, messages):
    aes = AESGCM(key)
    frames = []
    for i, m in enumerate(messages):
        nonce = i.to_bytes(12, "big")
        frames.append((nonce, aes.encrypt(nonce, m, None)))
    return frames


def _try_decrypt(key, frames):
    aes = AESGCM(key)
    try:
        return [aes.decrypt(nonce, ct, None) for nonce, ct in frames]
    except InvalidTag:
        return None


def run_standard(rng, log=print):
    """Toy 16-bit-RSA VPN, then the attacker's Shor break. Returns a result dict."""
    log("\n=== STANDARD MODE: toy 16-bit RSA key exchange ===")
    rsa = generate_rsa16(rng)
    session_key = bytes(rng.randrange(256) for _ in range(16))  # real 128-bit key
    wrapped = rsa_wrap_key(session_key, rsa["n"], rsa["e"])
    frames = _aes_traffic(session_key, SYNTHETIC_TRAFFIC)
    log(f"  Server public key : N={rsa['n']} ({rsa['n'].bit_length()} bits), e={rsa['e']}")
    log(f"  Handshake on wire : {len(wrapped)} RSA ciphertexts (the wrapped 128-bit session key)")
    log(f"  Traffic on wire   : {len(frames)} AES-128-GCM frames (unreadable without the key)")

    log("\n  [ATTACKER] recorded the handshake and the encrypted frames.")
    log("  [ATTACKER] cannot decrypt the frames, so he attacks the key exchange: factor N.")
    t0 = time.perf_counter()
    p, q, attempts = shor_factor(rsa["n"], rng, log=lambda s: log("  " + s))
    elapsed = time.perf_counter() - t0
    log(f"  [ATTACKER] Shor: N = {p} x {q}  ({attempts} attempt(s), {elapsed:.3f}s emulated)")

    phi = (p - 1) * (q - 1)
    d = pow(rsa["e"], -1, phi)
    recovered_key = rsa_unwrap_key(wrapped, rsa["n"], d)
    plaintext = _try_decrypt(recovered_key, frames)
    log(f"  [ATTACKER] rebuilt private key d={d}; recovered session key: {recovered_key.hex()}")
    log("\n  --- WHAT THE USER IS SENDING (as read by the attacker) ---")
    for line in plaintext or []:
        log("    > " + line.decode("utf-8"))
    return {"broken": plaintext == SYNTHETIC_TRAFFIC, "factors": (p, q),
            "recovered_key_ok": recovered_key == session_key, "plaintext": plaintext}


def run_quantum_safe(rng, log=print, guesses=20000):
    """ML-KEM-1024 session. The same attacker pipeline has nothing to attack."""
    log("\n=== QUANTUM-SAFE MODE: ML-KEM-1024 key exchange ===")
    pk, sk = mlkem.generate_keypair()
    ct, shared_secret = mlkem.encapsulate(pk)
    key = HKDF(hashes.SHA256(), 32, None, b"lab-quantum-session").derive(shared_secret)
    frames = _aes_traffic(key, SYNTHETIC_TRAFFIC)
    log(f"  Client public key : {len(pk)} bytes (ML-KEM-1024, lattice based)")
    log(f"  Handshake on wire : {len(ct)}-byte KEM ciphertext")
    log(f"  Traffic on wire   : {len(frames)} AES-256-GCM frames")

    log("\n  [ATTACKER] recorded the handshake and the encrypted frames.")
    log("  [ATTACKER] step 1: look for an integer modulus N to factor with Shor ... ")
    log("             public data = lattice vectors, no RSA/DH/ECC group, no N: nothing to factor.")
    log("  [ATTACKER] step 2: Shor needs a hidden period (a^x mod N). Module-LWE has no such")
    log("             period; no polynomial-time quantum algorithm for it is known.")
    log(f"  [ATTACKER] step 3: fall back to guessing the 256-bit key ({guesses} tries) ...")
    rg = random.Random(rng.random())
    cracked = any(_try_decrypt(bytes(rg.randrange(256) for _ in range(32)), frames[:1])
                  for _ in range(guesses))
    log(f"             result: {'KEY FOUND' if cracked else 'all guesses rejected by the GCM tag'} "
        f"(search space 2^256; even Grover leaves ~2^128)")
    legit = _try_decrypt(key, frames)
    log("\n  --- WHAT THE ATTACKER SEES ---")
    for i, (_, c) in enumerate(frames):
        log(f"    frame {i}: {c[:24].hex()}...  (ciphertext only)")
    log(f"  (legitimate endpoint decrypts correctly: {legit == SYNTHETIC_TRAFFIC})")
    return {"broken": cracked, "legit_ok": legit == SYNTHETIC_TRAFFIC}


def main():
    ap = argparse.ArgumentParser(description="Isolated Shor's-algorithm lab (synthetic data only)")
    ap.add_argument("--mode", choices=["standard", "quantum", "both"], default="both")
    ap.add_argument("--seed", type=int, default=None, help="reproducible run")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    print("LAB / SYNTHETIC DATA ONLY - isolated from the production VPN")
    print("Quantum step is emulated; see module docstring for scope and limits.")
    if args.mode in ("standard", "both"):
        run_standard(rng)
    if args.mode in ("quantum", "both"):
        run_quantum_safe(rng)


if __name__ == "__main__":
    main()
