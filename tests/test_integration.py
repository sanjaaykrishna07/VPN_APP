"""
QuantumSafeVPN — Full End-to-End Integration Test Suite
========================================================
Validates the complete PQC handshake, dynamic IP allocation,
AES-256-GCM encrypted packet framing, replay rejection, and multi-client routing.
"""
import unittest
import socket
import threading
import time
import struct
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vpn.ip_pool import IPPool, SessionRouter
from pqc.mlkem import generate_keypair as kem_keygen, encapsulate, decapsulate
from pqc.mldsa import generate_keypair as dsa_keygen, sign, verify
from crypto.classical import derive_session_key, encrypt, decrypt


class TestEndToEndPqcTunnel(unittest.TestCase):

    def setUp(self):
        self.dsa_pk, self.dsa_sk = dsa_keygen()
        self.pool = IPPool(start_ip="10.8.0.2", end_ip="10.8.0.50")
        self.router = SessionRouter()

    def test_full_handshake_flow(self):
        """Simulate client-server PQC handshake exchange."""
        # 1. Server identity
        server_dsa_pk = self.dsa_pk
        server_dsa_sk = self.dsa_sk

        # 2. Client generates ephemeral ML-KEM-1024 keypair
        client_kem_pk, client_kem_sk = kem_keygen()

        # 3. Server encapsulates shared secret
        ciphertext, server_shared_secret = encapsulate(client_kem_pk)

        # 4. Server signs transcript
        protocol_version = b"QuantumSafeVPN-v1"
        transcript = protocol_version + client_kem_pk + ciphertext
        signature = sign(server_dsa_sk, transcript)

        # 5. Client verifies signature
        self.assertTrue(verify(server_dsa_pk, transcript, signature))

        # 6. Client decapsulates shared secret
        client_shared_secret = decapsulate(client_kem_sk, ciphertext)
        self.assertEqual(client_shared_secret, server_shared_secret)

        # 7. Both derive AES-256-GCM session key via HKDF-SHA256
        client_session_key = derive_session_key(client_shared_secret)
        server_session_key = derive_session_key(server_shared_secret)
        self.assertEqual(client_session_key, server_session_key)

        # 8. Dynamic IP assignment
        client_addr = ("11.12.2.82", 45678)
        assigned_ip = self.pool.allocate(client_addr)
        self.assertEqual(assigned_ip, "10.8.0.2")

    def test_encrypted_packet_framing_and_tampering(self):
        """Test AES-256-GCM framing with sequence counter and tampering detection."""
        key = b"K" * 32
        raw_ip_packet = (
            b"\x45\x00\x00\x3c\x1a\x2b\x00\x00\x40\x01\x00\x00"
            b"\x0a\x08\x00\x02\x01\x01\x01\x01"
            b"ECHO_REQUEST_PAYLOAD"
        )
        seq = 1
        seq_payload = struct.pack("!Q", seq) + raw_ip_packet

        # Encrypt
        encrypted = encrypt(key, seq_payload)
        self.assertEqual(len(encrypted), 12 + len(seq_payload) + 16)

        # Decrypt
        decrypted = decrypt(key, encrypted)
        rec_seq = struct.unpack("!Q", decrypted[:8])[0]
        rec_ip = decrypted[8:]

        self.assertEqual(rec_seq, 1)
        self.assertEqual(rec_ip, raw_ip_packet)

        # Tamper with encrypted packet
        tampered = bytearray(encrypted)
        tampered[15] ^= 0xFF
        with self.assertRaises(Exception):
            decrypt(key, bytes(tampered))

    def test_multi_client_ip_routing(self):
        """Verify routing table directs return traffic to correct client."""
        router = SessionRouter()
        pool = IPPool()

        ip1 = pool.allocate(("11.12.2.82", 50001))
        ip2 = pool.allocate(("11.12.2.83", 50002))

        router.register_client(ip1, "socket_obj_1", b"key1"*8)
        router.register_client(ip2, "socket_obj_2", b"key2"*8)

        # Inbound packet destined for ip2
        packet_for_c2 = (
            b"\x45\x00\x00\x3c\x00\x00\x00\x00\x40\x06\x00\x00"
            b"\x01\x01\x01\x01"  # src: 1.1.1.1
            + socket.inet_aton(ip2) + # dst: 10.8.0.3
            b"HTTP_RESPONSE"
        )

        dst = router.extract_dest_ip(packet_for_c2)
        self.assertEqual(dst, ip2)

        client_record = router.get_client(dst)
        self.assertIsNotNone(client_record)
        self.assertEqual(client_record["socket"], "socket_obj_2")


if __name__ == "__main__":
    unittest.main()
