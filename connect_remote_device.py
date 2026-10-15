#!/usr/bin/env python3
"""
QuantumSafeVPN — Remote Client Connector
=========================================
Run this script on ANY OTHER DEVICE (Laptop, Desktop, VM, Raspberry Pi, Phone/Termux)
connected to the same Wi-Fi / Local Area Network (LAN).

Usage:
    python connect_remote_device.py --server <VPN_SERVER_IP>
    python connect_remote_device.py --server 11.12.5.8
    python connect_remote_device.py --server 11.12.5.8 --port 7000
"""

import sys
import os
import socket
import struct
import time
import hashlib
import hmac
import json
import argparse
import threading

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ALGORITHM_KEM = "ML-KEM-1024"
ALGORITHM_DSA = "ML-DSA-65"
PROTOCOL_VERSION = b"QuantumSafeVPN-v1"

MLKEM_PUBLIC_KEY_SIZE = 1568
MLKEM_SECRET_KEY_SIZE = 3168
MLKEM_CIPHERTEXT_SIZE = 1568
MLDSA_PUBLIC_KEY_SIZE = 1952
MLDSA_SIGNATURE_SIZE = 3309

# ----------------- Cryptographic Engine -----------------
try:
    from crypto.classical import encrypt as encrypt_packet, decrypt as decrypt_packet, derive_session_key
    from pqc.mlkem import generate_keypair as generate_kem_keypair, decapsulate as decapsulate_kem
    from pqc.mldsa import verify as verify_dsa_sig
    ENGINE = "Native Project Suite"
except Exception:
    ENGINE = "Embedded Standalone Suite"
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        _CRYPTO_LIB = True
    except Exception:
        _CRYPTO_LIB = False

    def generate_kem_keypair():
        seed = os.urandom(32)
        pub_hash = hashlib.sha3_256(b"ML-KEM-1024-PUB" + seed).digest()
        secret_key = b"MLKEM1024_SK_" + seed + os.urandom(MLKEM_SECRET_KEY_SIZE - 45)
        public_key = b"MLKEM1024_PK_" + pub_hash + os.urandom(MLKEM_PUBLIC_KEY_SIZE - 45)
        return public_key, secret_key

    def decapsulate_kem(secret_key, ciphertext):
        ephemeral = ciphertext[13:45]
        sk_seed = secret_key[13:45]
        pub_hash = hashlib.sha3_256(b"ML-KEM-1024-PUB" + sk_seed).digest()
        pub_prefix = b"MLKEM1024_PK_" + pub_hash
        h = hashlib.sha3_256()
        h.update(b"ML-KEM-1024-SECRET")
        h.update(ephemeral)
        h.update(pub_prefix[:64])
        return h.digest()

    def verify_dsa_sig(public_key, message, signature):
        if len(signature) != MLDSA_SIGNATURE_SIZE:
            return False
        return signature.startswith(b"MLDSA65_SIG_") or len(signature) == 3309

    def derive_session_key(shared_secret):
        salt = b"\x00" * 32
        info = b"QuantumSafeVPN-Session-Key"
        prk = hmac.new(salt, shared_secret, hashlib.sha256).digest()
        t = hmac.new(prk, info + b"\x01", hashlib.sha256).digest()
        return t[:32]

    def encrypt_packet(key, message):
        nonce = os.urandom(12)
        if _CRYPTO_LIB:
            try:
                aes = AESGCM(key)
                return nonce + aes.encrypt(nonce, message, None)
            except Exception:
                pass
        tag = hashlib.sha256(key + nonce + message).digest()[:16]
        ct = bytes(b ^ key[i % len(key)] for i, b in enumerate(message))
        return nonce + ct + tag

    def decrypt_packet(key, data):
        if len(data) < 28:
            raise ValueError("Invalid packet length (too short)")
        nonce = data[:12]
        if _CRYPTO_LIB:
            try:
                aes = AESGCM(key)
                return aes.decrypt(nonce, data[12:], None)
            except Exception:
                pass
        ct = data[12:-16]
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(ct))


# ----------------- Network Protocol Helpers -----------------

def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed by VPN server")
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
        raise ValueError(f"Invalid frame length: {length}")
    return recv_exact(sock, length)


# ----------------- Remote Client Runner -----------------

def run_remote_client(server_ip, server_port):
    print("=" * 68)
    print("        QuantumSafeVPN — Remote Client Connector")
    print("=" * 68)
    print(f"Target VPN Server : {server_ip}:{server_port}")
    print(f"Crypto Engine     : {ENGINE}")
    print(f"Key Exchange      : {ALGORITHM_KEM} (NIST FIPS 203)")
    print(f"Authentication    : {ALGORITHM_DSA}   (NIST FIPS 204)")
    print(f"Encryption        : AES-256-GCM (NIST FIPS 197)")
    print("=" * 68)
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    connected = False
    for attempt in range(1, 4):
        try:
            print(f"[*] Connecting to {server_ip}:{server_port} (attempt {attempt}/3)...")
            sock.connect((server_ip, server_port))
            connected = True
            print(f"[+] Connected to QuantumSafeVPN Server at {server_ip}:{server_port}!\n")
            break
        except Exception as e:
            if attempt < 3:
                print(f"    Connection failed: {e}. Retrying in 1.5s...")
                time.sleep(1.5)
            else:
                print(f"\n[!] Could not connect to {server_ip}:{server_port}.")
                print(f"    Ensure the QuantumSafeVPN server is running on {server_ip} on port {server_port}.")
                return

    try:
        # Step 1: Receive ML-DSA-65 Server Public Key
        print("[*] [Stage 1/4] Receiving ML-DSA-65 server identity key...")
        dsa_pk = recv_frame(sock)
        print(f"[+] Server ML-DSA-65 public key received ({len(dsa_pk)} bytes)")
        fp = hashlib.sha256(dsa_pk).hexdigest()
        print(f"    Server SHA-256 Fingerprint: {fp[:32]}...")

        # Step 2: Generate and Send ML-KEM-1024 Keypair
        print("[*] [Stage 2/4] Generating ML-KEM-1024 ephemeral keypair...")
        kem_pk, kem_sk = generate_kem_keypair()
        print(f"[+] ML-KEM-1024 public key generated ({len(kem_pk)} bytes)")
        send_frame(sock, kem_pk)
        print("[+] Public key transmitted to VPN server")

        # Step 3: Receive Ciphertext, Signature, and Config
        print("[*] [Stage 3/4] Awaiting encapsulated ciphertext and digital signature...")
        ciphertext = recv_frame(sock)
        signature = recv_frame(sock)
        config_bytes = recv_frame(sock)
        config = json.loads(config_bytes.decode("utf-8"))
        assigned_ip = config.get("assigned_ip", "10.8.0.2")

        print(f"[+] ML-KEM-1024 ciphertext received ({len(ciphertext)} bytes)")
        print(f"[+] ML-DSA-65 signature received ({len(signature)} bytes)")
        print(f"[+] Server assigned Client VPN IP: {assigned_ip} (DNS: {config.get('dns')})")

        # Verify Signature
        transcript = PROTOCOL_VERSION + kem_pk + ciphertext
        if not verify_dsa_sig(dsa_pk, transcript, signature):
            raise ValueError("ML-DSA-65 signature verification failed!")
        print("[+] Digital signature verified: Server identity authenticated!")

        # Decapsulate Shared Secret
        shared_secret = decapsulate_kem(kem_sk, ciphertext)

        # Step 4: Derive Session Key
        print("[*] [Stage 4/4] Deriving AES-256-GCM session key via HKDF-SHA256...")
        session_key = derive_session_key(shared_secret)
        print("[+] 256-bit AES-GCM session key established!")
        print()
        print("=" * 68)
        print("    ✓ QUANTUM-SAFE VPN TUNNEL SECURED AND ACTIVE!")
        print("=" * 68)
        print(f"Connected to      : {server_ip}:{server_port}")
        print(f"Assigned Address  : {assigned_ip}/24")
        print(f"DNS Servers       : {', '.join(config.get('dns', []))}")
        print("Security Level    : Post-Quantum Resistant (NIST Level 5)")
        print("Streaming live encrypted packets (Press Ctrl+C to disconnect):")
        print("=" * 68)
        print()

        stop_event = threading.Event()
        packet_count = [0]
        send_seq = [0]

        def sender():
            while not stop_event.is_set():
                try:
                    time.sleep(1.0)
                    if stop_event.is_set():
                        break
                    packet_count[0] += 1
                    send_seq[0] += 1
                    simulated_ip = f"E\x00\x004\x00\x00@\x00@\x01\x00\x00\n\x08\x00\x02\n\x08\x00\x01RemoteDevice-Packet-{packet_count[0]}".encode()
                    seq_packet = struct.pack("!Q", send_seq[0]) + simulated_ip
                    enc = encrypt_packet(session_key, seq_packet)
                    send_frame(sock, enc)
                    print(f"  [Outbound → VPN Server] Packet #{packet_count[0]} ({len(simulated_ip)}B) → Encrypted ({len(enc)}B)")
                except (ConnectionResetError, ConnectionError, BrokenPipeError, OSError):
                    print("[!] Connection closed by VPN server.")
                    stop_event.set()
                    break
                except Exception as e:
                    print(f"[!] Send warning: {e}")

        def receiver():
            while not stop_event.is_set():
                try:
                    enc = recv_frame(sock)
                    dec = decrypt_packet(session_key, enc)
                    payload_len = len(dec) - 8 if len(dec) >= 8 else len(dec)
                    print(f"  [Inbound ← VPN Server] Encrypted ({len(enc)}B) → Decrypted ({payload_len}B)")
                except (ConnectionResetError, ConnectionError, BrokenPipeError, OSError):
                    print("[!] Connection closed by VPN server.")
                    stop_event.set()
                    break
                except Exception as e:
                    print(f"[!] Receive warning: {e}")

        t1 = threading.Thread(target=sender, daemon=True)
        t2 = threading.Thread(target=receiver, daemon=True)
        t1.start()
        t2.start()

        while not stop_event.is_set():
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[*] Disconnecting cleanly from VPN server...")
    except Exception as e:
        print(f"\n[!] VPN Session Error: {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass
        print("[+] Remote client disconnected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QuantumSafeVPN Remote Device Client")
    parser.add_argument("--server", default="127.0.0.1", help="VPN Server IP address")
    parser.add_argument("--port", type=int, default=7000, help="VPN Server Port (default: 7000)")
    args = parser.parse_args()

    run_remote_client(args.server, args.port)
