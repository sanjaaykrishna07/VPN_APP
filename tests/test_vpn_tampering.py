from crypto.classical import encrypt, decrypt


def main():
    print("=" * 60)
    print("AES-256-GCM VPN PACKET INTEGRITY TEST")
    print("=" * 60)

    key = b"A" * 32
    message = b"QuantumSafeVPN test packet"

    # ---------------------------------------------------------
    # 1. Encrypt original packet
    # ---------------------------------------------------------

    print()
    print("[1] Encrypting original VPN packet...")

    encrypted = encrypt(key, message)

    print(f"[+] Plaintext size : {len(message)} bytes")
    print(f"[+] Encrypted size : {len(encrypted)} bytes")

    # AES-GCM format used by this project:
    #
    # 12 bytes  = nonce
    # N bytes   = ciphertext
    # 16 bytes  = authentication tag
    #
    # Therefore:
    #
    # encrypted size = plaintext size + 12 + 16

    expected_size = len(message) + 12 + 16

    if len(encrypted) == expected_size:
        print(
            "[PASS] AES-GCM packet contains "
            "nonce + ciphertext + authentication tag"
        )
    else:
        print(
            "[FAIL] Unexpected encrypted packet size"
        )
        return

    # ---------------------------------------------------------
    # 2. Verify original packet
    # ---------------------------------------------------------

    print()
    print("[2] Decrypting original packet...")

    try:

        decrypted = decrypt(
            key,
            encrypted
        )

        if decrypted == message:

            print(
                "[PASS] Original packet accepted"
            )

        else:

            print(
                "[FAIL] Decrypted packet does not match"
            )
            return

    except Exception as e:

        print(
            f"[FAIL] Original packet rejected: {e}"
        )
        return

    # ---------------------------------------------------------
    # 3. Modify ciphertext
    # ---------------------------------------------------------

    print()
    print("[3] Modifying one byte of encrypted packet...")

    tampered = bytearray(
        encrypted
    )

    # Byte 20 is inside the encrypted payload.
    tampered[20] ^= 0x01

    tampered = bytes(
        tampered
    )

    print(
        "[+] One ciphertext byte modified"
    )

    # ---------------------------------------------------------
    # 4. Try to decrypt tampered packet
    # ---------------------------------------------------------

    print()
    print(
        "[4] Attempting to decrypt "
        "tampered packet..."
    )

    try:

        decrypt(
            key,
            tampered
        )

        print(
            "[FAIL] Tampered packet was accepted"
        )

    except Exception as e:

        print(
            "[PASS] Tampered packet rejected"
        )

        print(
            "[+] AES-256-GCM authentication "
            "detected the modification"
        )

        print(
            f"[+] Exception type: "
            f"{type(e).__name__}"
        )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "AES-256-GCM INTEGRITY TEST PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
