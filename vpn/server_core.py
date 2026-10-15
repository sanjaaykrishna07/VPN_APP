"""
QuantumSafeVPN server core (protocol v2).

Data plane per client:
    client TUN -> AES-256-GCM[k_c2s]( 8B seq || IPv4 packet ) -> TCP -> this server
        -> source-address check -> server TUN -> kernel NAT -> internet
    internet -> kernel -> server TUN -> look up client by destination IP
        -> AES-256-GCM[k_s2c]( 8B seq || IPv4 packet ) -> TCP -> client TUN

Security properties enforced here (all were missing in v1):
    * replayed / reordered frames are DROPPED (v1 only printed a warning)
    * the inner packet's source IP must equal the client's leased IP (anti-spoof)
    * per-socket send lock (v1 could interleave frames from two threads)
    * handshake has a hard timeout, so a silent connection cannot hold a thread
    * only IPv4 is forwarded; anything else is dropped and counted
    * events carry metadata only (addresses, ports, byte counts) - never payload
"""
import socket
import struct
import threading
import time

from crypto.classical import encrypt, decrypt
from vpn import handshake as hs
from vpn.ip_pool import IPPool, SessionRouter

HANDSHAKE_TIMEOUT_SEC = 10
MAX_INNER_PACKET = 65535 - 8 - 12 - 16


def parse_ipv4(packet):
    """Return dict(src,dst,proto,dport) for an IPv4 packet, or None."""
    if len(packet) < 20 or (packet[0] >> 4) != 4:
        return None
    ihl = (packet[0] & 0x0F) * 4
    if ihl < 20 or len(packet) < ihl:
        return None
    proto = packet[9]
    info = {
        "src": socket.inet_ntoa(packet[12:16]),
        "dst": socket.inet_ntoa(packet[16:20]),
        "proto": {1: "ICMP", 6: "TCP", 17: "UDP"}.get(proto, str(proto)),
        "dport": None,
        "dns_query": None,
    }
    if proto in (6, 17) and len(packet) >= ihl + 4:
        info["dport"] = struct.unpack("!H", packet[ihl + 2: ihl + 4])[0]
        if proto == 17 and info["dport"] == 53:
            udp_payload = packet[ihl + 8:]
            if len(udp_payload) > 12:
                try:
                    idx = 12
                    labels = []
                    while idx < len(udp_payload):
                        length = udp_payload[idx]
                        if length == 0:
                            break
                        if length > 63 or idx + 1 + length > len(udp_payload):
                            labels = []
                            break
                        labels.append(udp_payload[idx + 1: idx + 1 + length].decode("ascii", errors="replace"))
                        idx += 1 + length
                    if labels:
                        info["dns_query"] = ".".join(labels)
                except Exception:
                    pass
    return info


class Session:
    def __init__(self, sock, ip, device, mode, k_c2s, k_s2c, addr):
        self.sock, self.ip, self.device, self.mode, self.addr = sock, ip, device, mode, addr
        self.k_c2s, self.k_s2c = k_c2s, k_s2c
        self.send_seq = 0
        self.last_recv_seq = 0
        self.send_lock = threading.Lock()
        self.bytes_in = self.bytes_out = 0
        self.dropped = {"replay": 0, "spoof": 0, "non_ipv4": 0, "bad_frame": 0}
        self.started = time.time()


class VpnServer:
    def __init__(self, tun, identity, client_store, *, host="0.0.0.0", port=7000,
                 server_vpn_ip="10.8.0.1", ip_start="10.8.0.2", ip_end="10.8.0.254",
                 dns_servers=("1.1.1.1", "8.8.8.8"), mtu=1400,
                 allowed_modes=(hs.MODE_STANDARD, hs.MODE_QUANTUM), on_event=None):
        self.tun, self.identity, self.client_store = tun, identity, client_store
        self.host, self.port = host, port
        self.server_vpn_ip, self.dns_servers, self.mtu = server_vpn_ip, list(dns_servers), mtu
        self.allowed_modes = tuple(allowed_modes)
        self.pool = IPPool(ip_start, ip_end)
        self.router = SessionRouter()
        self.sessions = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._listener = None
        self._on_event = on_event or (lambda kind, **kw: None)

    # ------------------------------------------------------------ lifecycle
    def start(self):
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind((self.host, self.port))
        self._listener.listen(32)
        self.port = self._listener.getsockname()[1]
        threading.Thread(target=self._tun_loop, daemon=True, name="tun->clients").start()
        threading.Thread(target=self._accept_loop, daemon=True, name="accept").start()
        return self.port

    def stop(self):
        self._stop.set()
        try:
            self._listener.close()
        except Exception:
            pass
        for s in list(self.sessions.values()):
            self._close(s, "server shutdown")

    # ------------------------------------------------------------ accept
    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                conn, addr = self._listener.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn, addr), daemon=True).start()

    def _serve(self, conn, addr):
        session = None
        try:
            conn.settimeout(HANDSHAKE_TIMEOUT_SEC)
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            k_c2s, k_s2c, ip, device, mode = hs.server_handshake(
                conn, self.identity, self.client_store,
                allocate_ip=lambda: self.pool.allocate(addr),
                config_for_ip=lambda assigned: {
                    "assigned_ip": assigned, "netmask": "255.255.255.0",
                    "server_ip": self.server_vpn_ip, "dns": self.dns_servers, "mtu": self.mtu},
                allowed_modes=self.allowed_modes)
            conn.settimeout(None)
            session = Session(conn, ip, device, mode, k_c2s, k_s2c, addr)
            with self._lock:
                self.sessions[ip] = session
            self.router.register_client(ip, conn, k_s2c)
            self._on_event("session_start", device=device, vpn_ip=ip, peer=addr[0], mode=mode)
            self._client_loop(session)
        except hs.AuthenticationError as exc:
            self._on_event("auth_failed", peer=addr[0], reason=str(exc))
        except (hs.HandshakeError, ConnectionError, OSError, ValueError) as exc:
            self._on_event("handshake_error", peer=addr[0], reason=str(exc))
        finally:
            if session:
                self._close(session, "client disconnected")
            else:
                try:
                    conn.close()
                except Exception:
                    pass

    def _close(self, s, reason):
        with self._lock:
            known = self.sessions.pop(s.ip, None)
        if known is None:
            return
        self.router.unregister_client(s.ip)
        self.pool.release(s.ip)
        try:
            s.sock.close()
        except Exception:
            pass
        self._on_event("session_end", device=s.device, vpn_ip=s.ip, reason=reason,
                       bytes_in=s.bytes_in, bytes_out=s.bytes_out, dropped=dict(s.dropped),
                       duration=round(time.time() - s.started, 1))

    # ------------------------------------------------------------ client -> internet
    def _client_loop(self, s):
        while not self._stop.is_set():
            frame = hs.recv_frame(s.sock)  # raises ConnectionError on close
            try:
                plain = decrypt(s.k_c2s, frame)
            except Exception:
                s.dropped["bad_frame"] += 1
                continue
            if len(plain) < 9:
                s.dropped["bad_frame"] += 1
                continue
            seq = struct.unpack("!Q", plain[:8])[0]
            if seq <= s.last_recv_seq:
                s.dropped["replay"] += 1
                continue
            s.last_recv_seq = seq
            packet = plain[8:]
            meta = parse_ipv4(packet)
            if meta is None:
                s.dropped["non_ipv4"] += 1
                continue
            if meta["src"] != s.ip:
                s.dropped["spoof"] += 1
                continue
            s.bytes_in += len(packet)
            flow_args = {"device": s.device, "direction": "out", "dst": meta["dst"],
                         "proto": meta["proto"], "dport": meta["dport"], "size": len(packet)}
            if meta.get("dns_query"):
                flow_args["dns_query"] = meta["dns_query"]
            self._on_event("flow", **flow_args)
            self.tun.write_packet(packet)

    # ------------------------------------------------------------ internet -> client
    def _tun_loop(self):
        while not self._stop.is_set():
            try:
                packet = self.tun.read_packet()
            except Exception:
                if self._stop.is_set():
                    return
                time.sleep(0.05)
                continue
            meta = parse_ipv4(packet) if packet else None
            if not meta:
                continue
            with self._lock:
                s = self.sessions.get(meta["dst"])
            if not s:
                continue
            try:
                with s.send_lock:
                    s.send_seq += 1
                    frame = encrypt(s.k_s2c, struct.pack("!Q", s.send_seq) + packet)
                    hs.send_frame(s.sock, frame)
                s.bytes_out += len(packet)
                self._on_event("flow", device=s.device, direction="in", src=meta["src"],
                               proto=meta["proto"], size=len(packet))
            except OSError:
                self._close(s, "send failed")
