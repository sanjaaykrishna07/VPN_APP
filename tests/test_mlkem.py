from pqc.mlkem import (
    generate_keypair,
    encapsulate,
    decapsulate
)


def test_mlkem():

    print("[*] Generating ML-KEM-1024 key pair...")

    public_key, secret_key = generate_keypair()

    print(
        f"[+] Public key size: {len(public_key)} bytes"
    )

    print(
        f"[+] Secret key size: {len(secret_key)} bytes"
    )

    print("[*] Encapsulating shared secret...")

    ciphertext, client_secret = encapsulate(
        public_key
    )

    print(
        f"[+] Ciphertext size: {len(ciphertext)} bytes"
    )

    print("[*] Decapsulating shared secret...")

    server_secret = decapsulate(
        secret_key,
        ciphertext
    )

    print(
        f"[+] Shared secret size: {len(client_secret)} bytes"
    )

    assert client_secret == server_secret

    print("[PASS] ML-KEM-1024 shared secrets match")


if __name__ == "__main__":
    test_mlkem()
