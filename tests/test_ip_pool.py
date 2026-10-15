"""
Tests for QuantumSafeVPN IP Pool & Session Routing
===================================================
"""
import unittest
from vpn.ip_pool import IPPool, SessionRouter


class TestIPPool(unittest.TestCase):

    def setUp(self):
        self.pool = IPPool(start_ip="10.8.0.2", end_ip="10.8.0.10")

    def test_allocation_and_release(self):
        # 1. Allocate first IP
        ip1 = self.pool.allocate(("192.168.1.50", 54321), "session-1")
        self.assertEqual(ip1, "10.8.0.2")

        # 2. Allocate second IP
        ip2 = self.pool.allocate(("192.168.1.51", 54322), "session-2")
        self.assertEqual(ip2, "10.8.0.3")

        # 3. Check active leases
        leases = self.pool.get_active_sessions()
        self.assertIn("10.8.0.2", leases)
        self.assertIn("10.8.0.3", leases)

        # 4. Release first IP and re-allocate
        self.pool.release("10.8.0.2")
        self.assertNotIn("10.8.0.2", self.pool.get_active_sessions())

        ip3 = self.pool.allocate(("192.168.1.52", 54323), "session-3")
        self.assertEqual(ip3, "10.8.0.2")

    def test_exhaustion(self):
        pool = IPPool(start_ip="10.8.0.2", end_ip="10.8.0.4")
        ips = [pool.allocate(("1.1.1.1", i), f"s-{i}") for i in range(3)]
        self.assertEqual(ips, ["10.8.0.2", "10.8.0.3", "10.8.0.4"])

        # 4th allocation should return None
        ip_none = pool.allocate(("1.1.1.1", 999), "s-overflow")
        self.assertIsNone(ip_none)


class TestSessionRouter(unittest.TestCase):

    def setUp(self):
        self.router = SessionRouter()

    def test_ip_extraction(self):
        # Sample IPv4 header (20 bytes): Version=4, IHL=5, Src=10.8.0.2, Dst=1.1.1.1
        sample_packet = (
            b"\x45\x00\x00\x3c\x1a\x2b\x00\x00\x40\x01\x00\x00"
            b"\x0a\x08\x00\x02"  # 10.8.0.2 (Src)
            b"\x01\x01\x01\x01"  # 1.1.1.1 (Dst)
            b"PING_DATA_PAYLOAD"
        )
        src = self.router.extract_src_ip(sample_packet)
        dst = self.router.extract_dest_ip(sample_packet)

        self.assertEqual(src, "10.8.0.2")
        self.assertEqual(dst, "1.1.1.1")


if __name__ == "__main__":
    unittest.main()
