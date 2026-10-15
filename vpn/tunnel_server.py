"""
QuantumSafeVPN production server (protocol v2).

Requires Linux, root/CAP_NET_ADMIN and /dev/net/tun. It REFUSES to start
otherwise - it never pretends to forward traffic.

Environment:
  VPN_SERVER_PORT     listen port (default 7000; use 443 to pass restrictive Wi-Fi)
  VPN_SERVER_HOST     bind address (default 0.0.0.0)
  VPN_KEY_DIR         directory holding the ML-DSA-65 identity (default ./keys)
  VPN_CLIENTS_FILE    enrolled-device store (default <VPN_KEY_DIR>/clients.json)
  VPN_ALLOWED_MODES   comma list: standard,quantum (default both)
  VPN_EVENT_LOG       JSONL metadata log (default logs/events.jsonl)
"""
import json
import logging
import os
import signal
import sys
import time
from logging.handlers import RotatingFileHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pqc.mldsa import load_or_create_server_identity, KEY_DIR  # noqa: E402
from vpn.config import load_config  # noqa: E402
from vpn.handshake import ClientStore, MODE_STANDARD, MODE_QUANTUM  # noqa: E402
from vpn.nat_manager import NATManager  # noqa: E402
from vpn.server_core import VpnServer  # noqa: E402
from vpn.tun import TunInterface, TunUnavailableError  # noqa: E402

# Keys that must never be written to a log, whatever a caller passes in.
_FORBIDDEN = {"token", "key", "payload", "password", "cookie", "secret", "data"}


def build_event_logger(path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    log = logging.getLogger("vpn.events")
    log.setLevel(logging.INFO)
    handler = RotatingFileHandler(path, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)

    def emit(kind, **fields):
        safe = {k: v for k, v in fields.items() if k.lower() not in _FORBIDDEN}
        log.info(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "event": kind, **safe}))
    return emit


def main():
    cfg = load_config()["server"]
    port = int(os.environ.get("VPN_SERVER_PORT", cfg.get("port", 7000)))
    modes = tuple(m.strip() for m in os.environ.get(
        "VPN_ALLOWED_MODES", f"{MODE_STANDARD},{MODE_QUANTUM}").split(",") if m.strip())
    clients_file = os.environ.get("VPN_CLIENTS_FILE", os.path.join(KEY_DIR, "clients.json"))
    emit = build_event_logger(os.environ.get("VPN_EVENT_LOG", "logs/events.jsonl"))

    store = ClientStore(clients_file)
    if not store._load():
        print(f"[!] No enrolled devices in {clients_file}. Enroll one first:\n"
              f"    python -m vpn.manage_clients add <device-name>")
        sys.exit(2)

    identity = load_or_create_server_identity()
    tun = TunInterface(cfg.get("tun_name", "tun0"), mtu=int(cfg.get("mtu", 1400)))
    try:
        tun.create()
        tun.configure(f"{cfg.get('server_ip', '10.8.0.1')}/24")
    except TunUnavailableError as exc:
        print(f"[FATAL] {exc}")
        sys.exit(3)

    nat = NATManager(vpn_subnet=cfg.get("tun_network", "10.8.0.0/24"), tun_interface=tun.name)
    if cfg.get("enable_nat", True) and not nat.setup_nat():
        print("[FATAL] NAT / IP forwarding could not be configured; refusing to start "
              "(clients would connect but reach nothing).")
        sys.exit(4)

    server = VpnServer(
        tun, identity, store, host=os.environ.get("VPN_SERVER_HOST", cfg.get("host", "0.0.0.0")),
        port=port, server_vpn_ip=cfg.get("server_ip", "10.8.0.1"),
        ip_start=cfg.get("client_ip_start", "10.8.0.2"), ip_end=cfg.get("client_ip_end", "10.8.0.254"),
        dns_servers=cfg.get("dns_servers", ["1.1.1.1", "8.8.8.8"]), mtu=int(cfg.get("mtu", 1400)),
        allowed_modes=modes, on_event=emit)
    server.start()
    emit("server_started", port=server.port, modes=",".join(modes))
    print(f"[+] QuantumSafeVPN v2 listening on :{server.port}  modes={','.join(modes)}")

    stop = {"flag": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(flag=True))
    try:
        while not stop["flag"]:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        nat.teardown_nat()
        tun.close()
        emit("server_stopped")


if __name__ == "__main__":
    main()
