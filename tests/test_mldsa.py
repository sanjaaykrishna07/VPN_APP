from pqc.mldsa import (
    generate_keypair,
    sign,
    verify
)


def main():

    message = b"QuantumSafeVPN authentication test"

    print("[*] Generating ML-DSA-65 key pair...")

    public_key, secret_key = generate_keypair()

    print(
        f"[+] Public key size: "
        f"{len(public_key)} bytes"
    )

    print(
        f"[+] Secret key size: "
        f"{len(secret_key)} bytes"
    )

    print("[*] Signing message...")

    signature = sign(
        secret_key,
        message
    )

    print(
        f"[+] Signature size: "
        f"{len(signature)} bytes"
    )

    print("[*] Verifying valid signature...")

    valid = verify(
        public_key,
        message,
        signature
    )

    if not valid:
        print("[FAIL] Valid signature rejected")
        return 1

    print("[PASS] Valid signature accepted")

    print("[*] Testing tampered message...")

    tampered_message = (
        b"QuantumSafeVPN authentication TEST"
    )

    tampered_valid = verify(
        public_key,
        tampered_message,
        signature
    )

    if tampered_valid:
        print("[FAIL] Tampered message accepted")
        return 1

    print("[PASS] Tampered message rejected")

    print()
    print("All ML-DSA-65 tests passed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
