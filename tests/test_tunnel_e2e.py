"""
End-to-end data-plane tests: real TCP sockets, real handshake, real AES-GCM
framing, real IPv4 packets. Only the kernel TUN is replaced by an in-memory pair
(tests need no root). Production code never uses this double.
Run:  python -m unittest tests.test_tunnel_e2e -v
"""
import os
import queue
import socket
import struct
import sys
import tempfile
import time
import unittest

_TMP = tempfile.mkdtemp(prefix="qsvpn-e2e-")
os.environ["VPN_KEY_DIR"] = _TMP
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pqc import mldsa  # noqa: E402
from vpn import handshake as hs  # noqa: E402
from vpn.server_core import VpnServer  # noqa: E402
from vpn.client_core import VpnClient  # noqa: E402
from crypto.classical import encrypt  # noqa: E402


class MemTun:
    """In-memory stand-in for a kernel TUN device (TEST ONLY)."""
    def __init__(self):
        self.rx, self.tx = queue.Queue(), queue.Queue()  # rx: read_packet, tx: write_packet

    def read_packet(self):
        try:
            return self.rx.get(timeout=0.2)
        except queue.Empty:
            return b""

    def write_packet(self, p):
        self.tx.put(p)


def ipv4(src, dst, proto=6, dport=443, payload=b"hello"):
    l4 = struct.pack("!HHII", 50000, dport, 0, 0) + payload if proto in (6, 17) else payload
    total = 20 + len(l4)
    hdr = struct.pack("!BBHHHBBH4s4s", 0x45, 0, total, 1, 0, 64, proto, 0,
                      socket.inet_aton(src), socket.inet_aton(dst))
    return hdr + l4


class TunnelE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identity = mldsa.load_or_create_server_identity()
        cls.store = hs.ClientStore(os.path.join(_TMP, "clients.json"))
        cls.token = cls.store.add_device("phone-1")
        cls.events = []
        cls.stun = MemTun()
        cls.server = VpnServer(cls.stun, cls.identity, cls.store, host="127.0.0.1", port=0,
                               on_event=lambda kind, **kw: cls.events.append((kind, kw)))
        cls.port = cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def _client(self, mode):
        ctun = MemTun()
        c = VpnClient(ctun, self.identity[0], "phone-1", self.token, mode=mode)
        c.connect("127.0.0.1", self.port)
        return c, ctun

    def _drain(self, q):
        out = []
        while True:
            try:
                out.append(q.get(timeout=0.4))
            except queue.Empty:
                return out

    def _roundtrip(self, mode):
        c, ctun = self._client(mode)
        try:
            self.assertTrue(c.connected)
            ip = c.config["assigned_ip"]
            out = ipv4(ip, "93.184.216.34", 6, 443, b"GET / (synthetic)")
            ctun.rx.put(out)  # app -> client TUN
            self.assertEqual(self.stun.tx.get(timeout=3), out, "server TUN must receive the exact packet")
            back = ipv4("93.184.216.34", ip, 6, 50000, b"HTTP/1.1 200 (synthetic)")
            self.stun.rx.put(back)  # internet -> server TUN
            self.assertEqual(ctun.tx.get(timeout=3), back, "client TUN must receive the exact reply")
        finally:
            c.close()

    def test_packets_flow_both_ways_standard_mode(self):
        self._roundtrip(hs.MODE_STANDARD)

    def test_packets_flow_both_ways_quantum_mode(self):
        self._roundtrip(hs.MODE_QUANTUM)

    def test_spoofed_source_is_dropped(self):
        c, ctun = self._client(hs.MODE_STANDARD)
        try:
            self._drain(self.stun.tx)
            ctun.rx.put(ipv4("10.8.0.99", "8.8.8.8"))  # not our leased IP
            self.assertEqual(self._drain(self.stun.tx), [], "spoofed packet must never reach the TUN")
        finally:
            c.close()

    def test_replayed_frame_is_dropped_not_forwarded(self):
        c, ctun = self._client(hs.MODE_STANDARD)
        try:
            self._drain(self.stun.tx)
            pkt = ipv4(c.config["assigned_ip"], "1.1.1.1", 17, 53, b"dns-query")
            ctun.rx.put(pkt)
            self.assertEqual(self.stun.tx.get(timeout=3), pkt)
            # attacker replays the exact captured frame (same seq) on the wire
            with c._send_lock:
                frame = encrypt(c.k_c2s, struct.pack("!Q", c.send_seq) + pkt)
                hs.send_frame(c.sock, frame)
            self.assertEqual(self._drain(self.stun.tx), [], "replayed frame must be dropped")
        finally:
            c.close()

    def test_wrong_token_never_gets_connected(self):
        c = VpnClient(MemTun(), self.identity[0], "phone-1", "f" * 64)
        with self.assertRaises(hs.AuthenticationError):
            c.connect("127.0.0.1", self.port)
        self.assertFalse(c.connected)

    def test_metadata_events_contain_no_payload(self):
        c, ctun = self._client(hs.MODE_STANDARD)
        try:
            ctun.rx.put(ipv4(c.config["assigned_ip"], "93.184.216.34", 6, 443, b"SECRET-PAYLOAD-MARKER"))
            self.stun.tx.get(timeout=3)
            time.sleep(0.2)
        finally:
            c.close()
        flows = [kw for kind, kw in self.events if kind == "flow" and kw.get("direction") == "out"]
        self.assertTrue(flows)
        self.assertTrue(any(f["dst"] == "93.184.216.34" and f["dport"] == 443 and f["proto"] == "TCP" for f in flows))
        self.assertNotIn("SECRET-PAYLOAD-MARKER", repr(self.events))

    def test_session_cleanup_releases_ip(self):
        before = len(self.server.pool.get_active_sessions())
        c, _ = self._client(hs.MODE_STANDARD)
        self.assertEqual(len(self.server.pool.get_active_sessions()), before + 1)
        c.close()
        deadline = time.time() + 3
        while time.time() < deadline and len(self.server.pool.get_active_sessions()) > before:
            time.sleep(0.1)
        self.assertEqual(len(self.server.pool.get_active_sessions()), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
