import socket
import threading
import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from pqc.mlkem import encapsulate
from crypto.classical import derive_session_key
from crypto.classical import encrypt
from crypto.classical import decrypt


HOST = "0.0.0.0"
PORT = 5000


def recv_exact(conn, size):
    data = b""

    while len(data) < size:
        chunk = conn.recv(size - len(data))

        if not chunk:
            raise ConnectionError(
                "Connection closed during reception"
            )

        data += chunk

    return data


def send_message(conn, data):
    length = len(data).to_bytes(4, "big")

    conn.sendall(length)
    conn.sendall(data)


def recv_message(conn):
    length = int.from_bytes(
        recv_exact(conn, 4),
        "big"
    )

    return recv_exact(conn, length)


def handle_client(conn, addr):

    print(f"[+] Client connected: {addr}")

    try:
        # ------------------------------------------------
        # ML-KEM HANDSHAKE
        # ------------------------------------------------

        print("[*] Waiting for ML-KEM-1024 public key...")

        # ML-KEM-1024 public key is received as a framed message
        client_public_key = recv_message(conn)

        print(
            f"[+] Received ML-KEM public key "
            f"({len(client_public_key)} bytes)"
        )

        # Server encapsulates a shared secret
        ciphertext, shared_secret = encapsulate(
            client_public_key
        )

        print("[+] ML-KEM encapsulation successful")

        # Send ciphertext back to client
        send_message(
            conn,
            ciphertext
        )

        print("[+] ML-KEM ciphertext sent")

        # Convert KEM secret into AES-256-GCM session key
        session_key = derive_session_key(
            shared_secret
        )

        print("[+] Session key derived")
        print("[+] AES-256-GCM secure channel established")

        # ------------------------------------------------
        # ENCRYPTED COMMUNICATION
        # ------------------------------------------------

        while True:

            encrypted_data = recv_message(conn)

            plaintext = decrypt(
                session_key,
                encrypted_data
            )

            message = plaintext.decode(
                "utf-8"
            )

            print(f"[CLIENT] {message}")

            if message.lower() == "exit":
                print("[*] Client requested disconnect")
                break

            response = (
                "Server received securely: "
                + message
            )

            encrypted_response = encrypt(
                session_key,
                response.encode("utf-8")
            )

            send_message(
                conn,
                encrypted_response
            )

    except Exception as e:

        print(f"[!] Client error: {e}")

    finally:

        conn.close()

        print(
            f"[-] Client disconnected: {addr}"
        )


def start_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind(
        (HOST, PORT)
    )

    server.listen(5)

    print("=" * 55)
    print("           QuantumSafe VPN Server")
    print("=" * 55)
    print(f"Listening on {HOST}:{PORT}")
    print("Mode: QUANTUM-SAFE")
    print("Key Exchange: ML-KEM-1024")
    print("Encryption: AES-256-GCM")
    print("=" * 55)

    while True:

        conn, addr = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        )

        thread.start()


if __name__ == "__main__":
    start_server()

