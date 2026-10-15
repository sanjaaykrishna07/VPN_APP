import socket
import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from pqc.mlkem import (
    generate_keypair,
    decapsulate
)

from crypto.classical import (
    derive_session_key,
    encrypt,
    decrypt
)


SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000


def recv_exact(sock, size):

    data = b""

    while len(data) < size:

        chunk = sock.recv(
            size - len(data)
        )

        if not chunk:
            raise ConnectionError(
                "Connection closed during reception"
            )

        data += chunk

    return data


def send_message(sock, data):

    length = len(data).to_bytes(
        4,
        "big"
    )

    sock.sendall(length)
    sock.sendall(data)


def recv_message(sock):

    length = int.from_bytes(
        recv_exact(sock, 4),
        "big"
    )

    return recv_exact(
        sock,
        length
    )


def start_client():

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    print("=" * 55)
    print("           QuantumSafe VPN Client")
    print("=" * 55)

    print(
        f"Connecting to "
        f"{SERVER_IP}:{SERVER_PORT}..."
    )

    client.connect(
        (SERVER_IP, SERVER_PORT)
    )

    print("[+] Connected to VPN server")

    # ------------------------------------------------
    # ML-KEM KEY GENERATION
    # ------------------------------------------------

    print("[*] Generating ML-KEM-1024 key pair...")

    public_key, secret_key = generate_keypair()

    print(
        f"[+] Public key generated "
        f"({len(public_key)} bytes)"
    )

    # Send public key to server
    send_message(
        client,
        public_key
    )

    print("[+] ML-KEM public key sent")

    # Receive encapsulated ciphertext
    ciphertext = recv_message(
        client
    )

    print(
        f"[+] Received ML-KEM ciphertext "
        f"({len(ciphertext)} bytes)"
    )

    # Decapsulate shared secret
    shared_secret = decapsulate(
        secret_key,
        ciphertext
    )

    print("[+] ML-KEM decapsulation successful")

    # Convert shared secret into AES key
    session_key = derive_session_key(
        shared_secret
    )

    print("[+] Session key derived")
    print("[+] AES-256-GCM secure channel established")
    print("[+] Quantum-safe channel ready")

    # ------------------------------------------------
    # ENCRYPTED COMMUNICATION
    # ------------------------------------------------

    while True:

        message = input("You: ")

        encrypted_data = encrypt(
            session_key,
            message.encode("utf-8")
        )

        send_message(
            client,
            encrypted_data
        )

        if message.lower() == "exit":
            break

        encrypted_response = recv_message(
            client
        )

        response = decrypt(
            session_key,
            encrypted_response
        )

        print(
            "Server:",
            response.decode("utf-8")
        )

    client.close()

    print("[-] Disconnected")


if __name__ == "__main__":
    start_client()
