"""
QuantumSafeVPN — Client IP Pool & Session Manager
==================================================
Manages dynamic IPv4 allocation for connected VPN clients and maintains
the active routing table mapping assigned VPN IPs to client sockets.
"""
import ipaddress
import struct
import threading
import time
from typing import Optional, Dict, Tuple, Any


class IPPool:
    """Thread-safe IP address pool for VPN clients."""

    def __init__(self, start_ip: str = "10.8.0.2", end_ip: str = "10.8.0.254", netmask: str = "255.255.255.0"):
        self.start_ip = ipaddress.IPv4Address(start_ip)
        self.end_ip = ipaddress.IPv4Address(end_ip)
        self.netmask = netmask
        self._lock = threading.Lock()
        
        # Available IPs set
        self._available = []
        curr = int(self.start_ip)
        end = int(self.end_ip)
        for val in range(curr, end + 1):
            self._available.append(str(ipaddress.IPv4Address(val)))
            
        # Active leases: ip_str -> { "client_addr": (ip, port), "assigned_at": timestamp, "session_id": str }
        self._leases: Dict[str, Dict[str, Any]] = {}

    def allocate(self, client_addr: Tuple[str, int], session_id: str = "") -> Optional[str]:
        """Allocate a free IP to a client."""
        with self._lock:
            if not self._available:
                return None
            assigned_ip = self._available.pop(0)
            self._leases[assigned_ip] = {
                "client_addr": client_addr,
                "assigned_at": time.time(),
                "session_id": session_id,
            }
            return assigned_ip

    def release(self, assigned_ip: str):
        """Release an allocated IP back to the pool."""
        with self._lock:
            if assigned_ip in self._leases:
                del self._leases[assigned_ip]
                if assigned_ip not in self._available:
                    self._available.append(assigned_ip)
                    # Keep pool sorted
                    self._available.sort(key=lambda ip: int(ipaddress.IPv4Address(ip)))

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._leases)


class SessionRouter:
    """
    Maintains active mapping between assigned VPN IPs and their connection sockets.
    Dispatches packets read from the TUN interface to the corresponding client socket.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # vpn_ip -> { "socket": sock, "session_key": bytes, "send_seq": int, "recv_seq": int }
        self._clients: Dict[str, Dict[str, Any]] = {}

    def register_client(self, vpn_ip: str, sock: Any, session_key: bytes):
        with self._lock:
            self._clients[vpn_ip] = {
                "socket": sock,
                "session_key": session_key,
                "send_seq": 0,
                "recv_seq": 0,
                "registered_at": time.time(),
            }

    def unregister_client(self, vpn_ip: str):
        with self._lock:
            if vpn_ip in self._clients:
                del self._clients[vpn_ip]

    def get_client(self, vpn_ip: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._clients.get(vpn_ip)

    def get_all_clients(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._clients)

    @staticmethod
    def extract_dest_ip(raw_packet: bytes) -> Optional[str]:
        """Extract destination IPv4 address from raw IP packet header."""
        if len(raw_packet) < 20:
            return None
        version = (raw_packet[0] >> 4) & 0x0F
        if version == 4:
            dest_bytes = raw_packet[16:20]
            return f"{dest_bytes[0]}.{dest_bytes[1]}.{dest_bytes[2]}.{dest_bytes[3]}"
        return None

    @staticmethod
    def extract_src_ip(raw_packet: bytes) -> Optional[str]:
        """Extract source IPv4 address from raw IP packet header."""
        if len(raw_packet) < 20:
            return None
        version = (raw_packet[0] >> 4) & 0x0F
        if version == 4:
            src_bytes = raw_packet[12:16]
            return f"{src_bytes[0]}.{src_bytes[1]}.{src_bytes[2]}.{src_bytes[3]}"
        return None
