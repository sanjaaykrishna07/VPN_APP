"""
Protocol v2 handshake tests over real TCP sockets (loopback).
Run:  python -m unittest tests.test_protocol_v2 -v
"""
import os
import socket
import sys
import tempfile
import threading
import unittest

_TMP = tempfile.mkdtemp(prefix="qsvpn-test-keys-")
os.environ["VPN_KEY_DIR"] = _TMP  # never touch the real keys/ directory

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pqc import mldsa  # noqa: E402
from vpn import handshake as hs  # noqa: E402
from crypto.classical import encrypt, decrypt  # noqa: E402


class ProtocolV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity = mldsa.load_or_create_server_identity()
        cls.store = hs.ClientStore(os.path.join(_TMP, "clients.json"))
        cls.token = cls.store.add_device("phone-1")

    def _run(self, client_fn, server_identity=None, allowed_modes=(hs.MODE_STANDARD, hs.MODE_QUANTUM)):
        """Start a one-shot server thread; return (client_result_or_exc, server_result_or_exc)."""
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        out = {}

        def server():
            conn, _ = listener.accept()
            conn.settimeout(5)
            try:
                out["server"] = hs.server_handshake(
                    conn, server_identity or self.identity, self.store,
                    allocate_ip=lambda: "10.8.0.2",
                    config_for_ip=lambda ip: {"assigned_ip": ip, "dns": ["1.1.1.1"], "mtu": 1400},
                    allowed_modes=allowed_modes,
                )
            except Exception as exc:
                out["server"] = exc
            finally:
                conn.close()

        t = threading.Thread(target=server)
        t.start()
        c = socket.create_connection(("127.0.0.1", port), timeout=5)
        try:
            out["client"] = client_fn(c)
        except Exception as exc:
            out["client"] = exc
        finally:
            c.close()
        t.join(10)
        listener.close()
        return out["client"], out["server"]

    def test_successful_handshake_and_directional_keys(self):
        client, server = self._run(
            lambda s: hs.client_handshake(s, self.identity[0], "phone-1", self.token))
        self.assertNotIsInstance(client, Exception, client)
        self.assertNotIsInstance(server, Exception, server)
        k_c2s, k_s2c, cfg = client
        s_c2s, s_s2c, ip, device, mode = server
        self.assertEqual(mode, hs.MODE_QUANTUM)
        self.assertEqual((k_c2s, k_s2c), (s_c2s, s_s2c))
        self.assertNotEqual(k_c2s, k_s2c, "directional keys must differ")
        self.assertEqual(cfg["assigned_ip"], "10.8.0.2")
        self.assertEqual(device, "phone-1")
        # a tunnel frame encrypted one way must not decrypt with the other direction's key
        frame = encrypt(k_c2s, b"\x00" * 8 + b"ip-packet")
        self.assertEqual(decrypt(s_c2s, frame)[8:], b"ip-packet")
        with self.assertRaises(Exception):
            decrypt(s_s2c, frame)

    def test_wrong_token_rejected_and_no_lease_allocated(self):
        leased = []
        listener = socket.socket(); listener.bind(("127.0.0.1", 0)); listener.listen(1)
        port = listener.getsockname()[1]
        result = {}

        def server():
            conn, _ = listener.accept(); conn.settimeout(5)
            try:
                hs.server_handshake(conn, self.identity, self.store,
                                    allocate_ip=lambda: leased.append(1) or "10.8.0.9",
                                    config_for_ip=lambda ip: {})
            except Exception as exc:
                result["server"] = exc
            finally:
                conn.close()

        t = threading.Thread(target=server); t.start()
        c = socket.create_connection(("127.0.0.1", port), timeout=5)
        with self.assertRaises(hs.AuthenticationError):
            hs.client_handshake(c, self.identity[0], "phone-1", "0" * 64)
        c.close(); t.join(10); listener.close()
        self.assertIsInstance(result["server"], hs.AuthenticationError)
        self.assertEqual(leased, [], "IP must not be allocated before authentication")

    def test_unknown_device_rejected(self):
        client, server = self._run(
            lambda s: hs.client_handshake(s, self.identity[0], "nobody", self.token))
        self.assertIsInstance(server, hs.AuthenticationError)

    def test_wrong_server_key_pin_rejected(self):
        other_pub, _ = mldsa.generate_keypair()
        client, _ = self._run(
            lambda s: hs.client_handshake(s, other_pub, "phone-1", self.token))
        self.assertIsInstance(client, hs.ServerIdentityError)

    def test_missing_pin_rejected(self):
        client, _ = self._run(lambda s: hs.client_handshake(s, b"", "phone-1", self.token))
        self.assertIsInstance(client, hs.ServerIdentityError)

    def test_forged_signature_from_old_standin_is_rejected(self):
        """Old v1 accepted any signature starting with b'MLDSA65_SIG_'."""
        forged = b"MLDSA65_SIG_" + b"\x00" * (mldsa.MLDSA_SIGNATURE_SIZE - 12)
        self.assertFalse(mldsa.verify(self.identity[0], b"anything", forged))

    def test_tampered_signature_rejected(self):
        sig = bytearray(mldsa.sign(self.identity[1], b"msg"))
        sig[100] ^= 0x01
        self.assertFalse(mldsa.verify(self.identity[0], b"msg", bytes(sig)))

    def test_passive_observer_cannot_recompute_secret(self):
        """The v1 attack recomputed SHA3(label||eph||pk[:45]) from wire data."""
        import hashlib
        from pqc.mlkem import generate_keypair, encapsulate
        pk, _ = generate_keypair()
        ct, ss = encapsulate(pk)
        h = hashlib.sha3_256(); h.update(b"ML-KEM-1024-SECRET"); h.update(ct[13:45]); h.update(pk[:45])
        self.assertNotEqual(h.digest(), ss)

    def test_standard_mode_works_without_pqc(self):
        client, server = self._run(
            lambda s: hs.client_handshake(s, self.identity[0], "phone-1", self.token, mode=hs.MODE_STANDARD))
        self.assertNotIsInstance(client, Exception, client)
        self.assertNotIsInstance(server, Exception, server)
        self.assertEqual(server[4], hs.MODE_STANDARD)
        self.assertEqual((client[0], client[1]), (server[0], server[1]))

    def test_server_policy_can_refuse_standard_mode(self):
        client, server = self._run(
            lambda s: hs.client_handshake(s, self.identity[0], "phone-1", self.token, mode=hs.MODE_STANDARD),
            allowed_modes=(hs.MODE_QUANTUM,))
        self.assertIsInstance(server, hs.HandshakeError)
        self.assertIsInstance(client, Exception)

    def test_downgrade_by_man_in_the_middle_is_detected(self):
        """Attacker flips the client's hello Q->S; signature over the transcript must then fail."""
        listener = socket.socket(); listener.bind(("127.0.0.1", 0)); listener.listen(1)
        server_port = listener.getsockname()[1]
        mitm = socket.socket(); mitm.bind(("127.0.0.1", 0)); mitm.listen(1)
        mitm_port = mitm.getsockname()[1]
        out = {}

        def server():
            conn, _ = listener.accept(); conn.settimeout(5)
            try:
                hs.server_handshake(conn, self.identity, self.store, lambda: "10.8.0.2", lambda ip: {})
            except Exception as exc:
                out["server"] = exc
            finally:
                conn.close()

        def relay():
            c, _ = mitm.accept(); c.settimeout(5)
            s = socket.create_connection(("127.0.0.1", server_port), timeout=5)
            hello = hs.recv_frame(c)
            hs.send_frame(s, hello[:-1] + b"S")  # downgrade attempt
            try:
                for _ in range(3):  # server pk, then relay client key
                    pass
                hs.send_frame(c, hs.recv_frame(s))        # server dsa pk -> client
                hs.send_frame(s, hs.recv_frame(c))        # client key -> server (wrong size for X25519)
            except Exception:
                pass
            finally:
                c.close(); s.close()

        threads = [threading.Thread(target=server), threading.Thread(target=relay)]
        for t in threads: t.start()
        c = socket.create_connection(("127.0.0.1", mitm_port), timeout=5)
        with self.assertRaises(Exception):
            hs.client_handshake(c, self.identity[0], "phone-1", self.token, mode=hs.MODE_QUANTUM)
        c.close()
        for t in threads: t.join(10)
        listener.close(); mitm.close()

    def test_token_store_never_contains_plaintext_token(self):
        with open(self.store.path, encoding="utf-8") as f:
            raw = f.read()
        self.assertNotIn(self.token, raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
