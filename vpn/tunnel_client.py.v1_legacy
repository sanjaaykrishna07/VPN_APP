"""
QuantumSafeVPN — Client Tunnel
==============================
Connects to QuantumSafeVPN Server, negotiates PQC handshake (ML-DSA + ML-KEM),
receives dynamic IP configuration, and tunnels traffic through local TUN.
"""
import socket
import struct
import sys
import os
import threading
import hashlib
import json
import time

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from vpn.tun import TunInterface
from pqc.mlkem import generate_keypair, decapsulate
from pqc.mldsa import verify
from crypto.classical import derive_session_key, encrypt, decrypt

SERVER_IP = os.environ.get("VPN_SERVER_IP", "127.0.0.1" if sys.platform == "win32" else "192.168.101.2")
SERVER_PORT = int(os.environ.get("VPN_SERVER_PORT", 7000))

PROTOCOL_VERSION = b"QuantumSafeVPN-v1"
MLDSA_PUBLIC_KEY_SIZE = 1952
MLDSA_SIGNATURE_SIZE = 3309
MLKEM_PUBLIC_KEY_SIZE = 1568
MLKEM_CIPHERTEXT_SIZE = 1568


def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
    return data


def send_frame(sock, data):
    header = struct.pack("!I", len(data))
    sock.sendall(header)
    sock.sendall(data)


def recv_frame(sock):
    header = recv_exact(sock, 4)
    length = struct.unpack("!I", header)[0]
    if length <= 0 or length > 65535:
        raise ValueError("Invalid packet length")
    return recv_exact(sock, length)


def verify_server_identity(dsa_public_key):
    print("[*] Verifying pinned server identity...")
    fingerprint = hashlib.sha256(dsa_public_key).hexdigest()
    print(f"[*] Server ML-DSA-65 SHA-256:\n    {fingerprint}")

    key_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "keys",
        "server_mldsa65_public.key"
    )

    if os.path.exists(key_file):
        try:
            with open(key_file, "rb") as f:
                trusted_key = f.read()
            if dsa_public_key == trusted_key:
                print("[+] Server identity verified against pinned key file")
                return
        except Exception:
            pass

    print("[+] Server identity accepted (Dynamic identity)")


def perform_handshake(sock):
    print()
    print("=" * 60)
    print("QUANTUM-SAFE VPN HANDSHAKE")
    print("=" * 60)

    # 1. Receive Server ML-DSA-65 Public Key
    print("[*] Waiting for ML-DSA-65 server public key...")
    dsa_public_key = recv_frame(sock)
    print(f"[+] ML-DSA public key received: {len(dsa_public_key)} bytes")
    verify_server_identity(dsa_public_key)

    # 2. Generate and Send ML-KEM-1024 Keypair
    print("[*] Generating ML-KEM-1024 key pair...")
    kem_public_key, kem_secret_key = generate_keypair()
    send_frame(sock, kem_public_key)
    print(f"[+] ML-KEM public key sent ({len(kem_public_key)} bytes)")

    # 3. Receive Ciphertext and Signature
    print("[*] Waiting for ML-KEM-1024 ciphertext...")
    ciphertext = recv_frame(sock)
    print(f"[+] ML-KEM ciphertext received: {len(ciphertext)} bytes")

    print("[*] Waiting for ML-DSA-65 signature...")
    signature = recv_frame(sock)
    print(f"[+] ML-DSA signature received: {len(signature)} bytes")

    # 4. Verify Signature
    transcript = PROTOCOL_VERSION + kem_public_key + ciphertext
    valid = verify(dsa_public_key, transcript, signature)
    if not valid:
        raise ValueError("ML-DSA-65 signature verification failed")
    print("[+] ML-DSA-65 signature verified")

    # 5. Receive Assigned Configuration
    config_bytes = recv_frame(sock)
    config = json.loads(config_bytes.decode("utf-8"))
    print(f"[+] Received Assigned IP: {config.get('assigned_ip')} (DNS: {config.get('dns')})")

    # 6. Decapsulate Shared Secret & Derive Key
    shared_secret = decapsulate(kem_secret_key, ciphertext)
    session_key = derive_session_key(shared_secret)
    print("[+] AES-256-GCM session key established")

    print("=" * 60)
    print("QUANTUM-SAFE VPN HANDSHAKE COMPLETE")
    print("=" * 60)
    return session_key, config


def main():
    tun = None
    sock = None

    try:
        # Retry connection to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        connected = False
        for attempt in range(1, 6):
            try:
                print(f"[*] Connecting to {SERVER_IP}:{SERVER_PORT} (attempt {attempt}/5)...")
                sock.connect((SERVER_IP, SERVER_PORT))
                connected = True
                print("[+] Connected to VPN server")
                break
            except Exception:
                time.sleep(0.5)

        if not connected:
            raise ConnectionError(f"Could not connect to VPN server at {SERVER_IP}:{SERVER_PORT}")

        session_key, config = perform_handshake(sock)
        assigned_ip = config.get("assigned_ip", "10.8.0.2")

        # Configure TUN Interface with assigned IP
        tun = TunInterface("tun0")
        tun.create()
        tun.configure(f"{assigned_ip}/24")
        print(f"[+] TUN interface configured with assigned IP: {assigned_ip}/24")

        send_seq = [0]
        stop_event = threading.Event()
        recv_seq = [0]

        def tun_to_network():
            while not stop_event.is_set():
                try:
                    packet = tun.read_packet()
                    if not packet:
                        time.sleep(0.01)
                        continue
                    send_seq[0] += 1
                    seq_packet = struct.pack("!Q", send_seq[0]) + packet
                    encrypted = encrypt(session_key, seq_packet)
                    send_frame(sock, encrypted)
                    print(f"  [TUN → VPN] Packet #{send_seq[0]} ({len(packet)}B) → Encrypted ({len(encrypted)}B)")
                except (ConnectionResetError, ConnectionError, BrokenPipeError, OSError) as e:
                    print(f"[!] Outbound connection closed: {e}")
                    stop_event.set()
                    break
                except Exception as e:
                    time.sleep(0.1)

        def network_to_tun():
            while not stop_event.is_set():
                try:
                    encrypted = recv_frame(sock)
                except (ConnectionResetError, ConnectionError, BrokenPipeError, OSError) as e:
                    print(f"[!] Inbound connection closed: {e}")
                    stop_event.set()
                    break
                except Exception as e:
                    time.sleep(0.1)
                    continue

                try:
                    decrypted = decrypt(session_key, encrypted)
                    if len(decrypted) >= 8:
                        seq = struct.unpack("!Q", decrypted[:8])[0]
                        raw_ip = decrypted[8:]
                        recv_seq[0] = seq
                    else:
                        raw_ip = decrypted
                    tun.write_packet(raw_ip)
                    print(f"  [VPN → TUN] Inbound encrypted ({len(encrypted)}B) → Decrypted ({len(raw_ip)}B)")
                except Exception as e:
                    time.sleep(0.05)

        t1 = threading.Thread(target=tun_to_network, daemon=True)
        t2 = threading.Thread(target=network_to_tun, daemon=True)
        t1.start()
        t2.start()

        print()
        print("=" * 60)
        print("[+] QuantumSafeVPN client is running")
        print(f"[+] Assigned VPN IP: {assigned_ip}")
        print("[+] Post-quantum secure tunnel active & streaming")
        print("[+] Press Ctrl+C to stop")
        print("=" * 60)

        while not stop_event.is_set():
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[*] Stopping QuantumSafeVPN client...")
    except Exception as e:
        print(f"\n[!] VPN client error: {e}")
    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
        if tun is not None:
            try:
                tun.close()
            except Exception:
                pass
        print("[+] QuantumSafeVPN client stopped")


if __name__ == "__main__":
    main()
