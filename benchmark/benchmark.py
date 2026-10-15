"""
QuantumSafeVPN — Empirical Post-Quantum Cryptography & Throughput Benchmark
===========================================================================
Measures actual execution times and throughputs for all PQC and classical
primitives without synthetic or hardcoded numbers.
"""
import time
import os
import sys
import json
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pqc import mlkem, mldsa
from crypto import classical


def benchmark_operation(name: str, func, iterations: int = 50) -> Dict[str, Any]:
    """Execute a function repeatedly and compute exact timing statistics."""
    # Warmup
    for _ in range(max(1, iterations // 10)):
        func()

    start = time.perf_counter()
    for _ in range(iterations):
        func()
    total_time = time.perf_counter() - start

    avg_ms = (total_time / iterations) * 1000.0
    ops_per_sec = iterations / total_time if total_time > 0 else 0.0

    return {
        "operation": name,
        "iterations": iterations,
        "total_seconds": round(total_time, 4),
        "avg_ms": round(avg_ms, 3),
        "ops_per_sec": round(ops_per_sec, 1),
    }


def run_benchmarks() -> Dict[str, Any]:
    print("=" * 72)
    print("      QuantumSafeVPN — Empirical Cryptographic Benchmark Suite")
    print("=" * 72)
    print(f"{'Algorithm & Operation':<35} | {'Avg Time (ms)':<15} | {'Ops / Sec':<15}")
    print("-" * 72)

    results = {}

    # 1. ML-KEM-1024 (NIST FIPS 203)
    kem_keys = mlkem.generate_keypair()
    pk, sk = kem_keys
    enc_ct, enc_ss = mlkem.encapsulate(pk)

    b_kem_keygen = benchmark_operation("ML-KEM-1024 KeyGen", mlkem.generate_keypair, 30)
    b_kem_encap = benchmark_operation("ML-KEM-1024 Encapsulate", lambda: mlkem.encapsulate(pk), 30)
    b_kem_decap = benchmark_operation("ML-KEM-1024 Decapsulate", lambda: mlkem.decapsulate(sk, enc_ct), 30)

    for b in [b_kem_keygen, b_kem_encap, b_kem_decap]:
        print(f"{b['operation']:<35} | {b['avg_ms']:<15.3f} | {b['ops_per_sec']:<15.1f}")
    results["mlkem_1024"] = [b_kem_keygen, b_kem_encap, b_kem_decap]

    # 2. ML-DSA-65 (NIST FIPS 204)
    dsa_keys = mldsa.generate_keypair()
    dpk, dsk = dsa_keys
    test_msg = b"QuantumSafeVPN Benchmark Handshake Transcript Message"
    sig = mldsa.sign(dsk, test_msg)

    b_dsa_keygen = benchmark_operation("ML-DSA-65 KeyGen", mldsa.generate_keypair, 20)
    b_dsa_sign = benchmark_operation("ML-DSA-65 Sign (Handshake)", lambda: mldsa.sign(dsk, test_msg), 20)
    b_dsa_verify = benchmark_operation("ML-DSA-65 Verify (Handshake)", lambda: mldsa.verify(dpk, test_msg, sig), 20)

    for b in [b_dsa_keygen, b_dsa_sign, b_dsa_verify]:
        print(f"{b['operation']:<35} | {b['avg_ms']:<15.3f} | {b['ops_per_sec']:<15.1f}")
    results["mldsa_65"] = [b_dsa_keygen, b_dsa_sign, b_dsa_verify]

    # 3. HKDF-SHA256 (RFC 5869)
    session_key = classical.derive_session_key(enc_ss)
    b_hkdf = benchmark_operation("HKDF-SHA256 Session KDF", lambda: classical.derive_session_key(enc_ss), 100)
    print(f"{b_hkdf['operation']:<35} | {b_hkdf['avg_ms']:<15.3f} | {b_hkdf['ops_per_sec']:<15.1f}")
    results["hkdf_sha256"] = [b_hkdf]

    # 4. AES-256-GCM (NIST FIPS 197) at standard MTU (1400 bytes)
    packet_1400 = b"\x45\x00" + os.urandom(1398)
    enc_1400 = classical.encrypt(session_key, packet_1400)

    b_aes_enc = benchmark_operation("AES-256-GCM Encrypt (1400B MTU)", lambda: classical.encrypt(session_key, packet_1400), 200)
    b_aes_dec = benchmark_operation("AES-256-GCM Decrypt (1400B MTU)", lambda: classical.decrypt(session_key, enc_1400), 200)

    # Compute actual crypto throughput (MB/s)
    enc_throughput_mb_s = (1400 * b_aes_enc["ops_per_sec"]) / (1024 * 1024)
    dec_throughput_mb_s = (1400 * b_aes_dec["ops_per_sec"]) / (1024 * 1024)

    print(f"{b_aes_enc['operation']:<35} | {b_aes_enc['avg_ms']:<15.3f} | {b_aes_enc['ops_per_sec']:<15.1f} ({enc_throughput_mb_s:.2f} MB/s)")
    print(f"{b_aes_dec['operation']:<35} | {b_aes_dec['avg_ms']:<15.3f} | {b_aes_dec['ops_per_sec']:<15.1f} ({dec_throughput_mb_s:.2f} MB/s)")
    results["aes_256_gcm"] = [b_aes_enc, b_aes_dec]

    # Save to benchmark/results/
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "benchmark_latest.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("=" * 72)
    print(f"[+] Benchmark measurements recorded to: {out_file}")
    print("=" * 72)
    return results


if __name__ == "__main__":
    run_benchmarks()
