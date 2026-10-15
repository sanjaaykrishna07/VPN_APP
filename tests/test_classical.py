from crypto.classical import generate_keypair
from crypto.classical import derive_key
from crypto.classical import encrypt
from crypto.classical import decrypt


def test_key_exchange():

    client_private, client_public = generate_keypair()
    server_private, server_public = generate_keypair()

    client_key = derive_key(
        client_private,
        server_public
    )

    server_key = derive_key(
        server_private,
        client_public
    )

    assert client_key == server_key

    print("[PASS] X25519 shared keys match")


def test_encryption():

    client_private, client_public = generate_keypair()
    server_private, server_public = generate_keypair()

    client_key = derive_key(
        client_private,
        server_public
    )

    server_key = derive_key(
        server_private,
        client_public
    )

    message = b"QuantumSafe VPN"

    encrypted = encrypt(
        client_key,
        message
    )

    decrypted = decrypt(
        server_key,
        encrypted
    )

    assert decrypted == message

    print("[PASS] AES-256-GCM encryption/decryption works")


def test_tampering():

    private1, public1 = generate_keypair()
    private2, public2 = generate_keypair()

    key1 = derive_key(
        private1,
        public2
    )

    key2 = derive_key(
        private2,
        public1
    )

    message = b"Secure VPN message"

    encrypted = encrypt(
        key1,
        message
    )

    tampered = bytearray(encrypted)
    tampered[-1] ^= 1

    try:

        decrypt(
            key2,
            bytes(tampered)
        )

        assert False

    except Exception:

        print("[PASS] Tampered ciphertext rejected")


if __name__ == "__main__":

    test_key_exchange()
    test_encryption()
    test_tampering()

    print("\nAll classical cryptography tests passed.")
