"""
QuantumSafeVPN client core (protocol v2) for Linux/desktop use.
The Android app implements the same wire protocol in Kotlin.
"""
import socket
import struct
import threading

from crypto.classical import encrypt, decrypt
from vpn import handshake as hs


class VpnClient:
    def __init__(self, tun, pinned_server_key, device, token, mode=hs.MODE_QUANTUM, on_event=None):
        self.tun, self.pinned, self.device, self.token, self.mode = tun, pinned_server_key, device, token, mode
        self._on_event = on_event or (lambda kind, **kw: None)
        self.sock = None
        self.config = None
        self.send_seq = 0
        self.last_recv_seq = 0
        self.dropped_replays = 0
        self.bytes_out = self.bytes_in = 0
        self._send_lock = threading.Lock()
        self._stop = threading.Event()
        self.connected = False

    def connect(self, host, port, timeout=10):
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            self.k_c2s, self.k_s2c, self.config = hs.client_handshake(
                sock, self.pinned, self.device, self.token, mode=self.mode)
        except Exception:
            sock.close()
            raise
        sock.settimeout(None)
        self.sock = sock
        self.connected = True  # set only after the authenticated handshake has really completed
        threading.Thread(target=self._tun_to_net, daemon=True).start()
        threading.Thread(target=self._net_to_tun, daemon=True).start()
        self._on_event("connected", assigned_ip=self.config["assigned_ip"], mode=self.mode)
        return self.config

    def _tun_to_net(self):
        while not self._stop.is_set():
            try:
                packet = self.tun.read_packet()
                if not packet:
                    continue
                with self._send_lock:
                    self.send_seq += 1
                    frame = encrypt(self.k_c2s, struct.pack("!Q", self.send_seq) + packet)
                    hs.send_frame(self.sock, frame)
                self.bytes_out += len(packet)
            except Exception:
                self._shutdown("outbound stopped")
                return

    def _net_to_tun(self):
        while not self._stop.is_set():
            try:
                plain = decrypt(self.k_s2c, hs.recv_frame(self.sock))
            except (ConnectionError, OSError, ValueError):
                self._shutdown("server closed connection")
                return
            except Exception:
                continue  # bad tag: drop the frame
            if len(plain) < 9:
                continue
            seq = struct.unpack("!Q", plain[:8])[0]
            if seq <= self.last_recv_seq:
                self.dropped_replays += 1
                continue
            self.last_recv_seq = seq
            self.bytes_in += len(plain) - 8
            self.tun.write_packet(plain[8:])

    def _shutdown(self, reason):
        if self._stop.is_set():
            return
        self._stop.set()
        self.connected = False
        try:
            self.sock.close()
        except Exception:
            pass
        self._on_event("disconnected", reason=reason)

    def close(self):
        self._shutdown("user requested")
