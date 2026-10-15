#!/usr/bin/env python3
"""
QuantumSafe VPN — Live Real-Time Server Network Monitor (Phase 6).

Streams real-time operational events from the VPN server's structured log
(logs/events.jsonl). Displays genuine observable network metadata:
  - Connection timestamps
  - Client device identifier & assigned VPN IP
  - Flow destination IP & destination port
  - Protocol (TCP / UDP / ICMP)
  - Observable cleartext DNS queries (UDP/53 questions)
  - Bytes sent and received
  - Session lifecycle (start, end, duration, dropped packet counts)
  - Authentication errors and handshake diagnostics

Privacy & Cryptographic Truth:
  TLS/HTTPS traffic is end-to-end encrypted between the client and destination.
  This monitor displays only genuine observable network-layer metadata and does
  NOT claim to inspect encrypted application payloads, search terms, or passwords.
"""
import json
import os
import sys
import time

LOG_FILE = os.environ.get("VPN_EVENT_LOG", os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "events.jsonl"
))

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def format_bytes(b):
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"


def print_banner():
    print(f"{CYAN}{BOLD}" + "=" * 80 + f"{RESET}")
    print(f"{CYAN}{BOLD}   QUANTUMSAFE VPN — REAL-TIME NETWORK & SECURITY MONITOR{RESET}")
    print(f"{DIM}   Wire Protocol: QuantumSafeVPN-v2 | Modes: ML-KEM-1024 / X25519 | ML-DSA-65{RESET}")
    print(f"{DIM}   Log Source: {LOG_FILE}{RESET}")
    print(f"{CYAN}{BOLD}" + "=" * 80 + f"{RESET}")
    print(f"{YELLOW}[NOTICE] HTTPS/TLS payloads remain end-to-end encrypted.{RESET}")
    print(f"{YELLOW}         Displaying verified transport metadata, flow telemetry, & DNS queries.{RESET}")
    print(f"{CYAN}" + "-" * 80 + f"{RESET}\n")


def render_event(raw_line):
    line = raw_line.strip()
    if not line:
        return
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        return

    ts = ev.get("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    # Shorten timestamp to HH:MM:SS
    time_str = ts.split("T")[-1][:8] if "T" in ts else ts[:8]
    kind = ev.get("event", "unknown")

    if kind == "server_started":
        port = ev.get("port")
        modes = ev.get("modes", "standard,quantum")
        print(f"[{time_str}] {GREEN}{BOLD}[SERVER ONLINE]{RESET} Listening on port {port} (Modes: {modes})")

    elif kind == "server_stopped":
        print(f"[{time_str}] {YELLOW}{BOLD}[SERVER STOPPED]{RESET} Server shutdown gracefully.")

    elif kind == "session_start":
        dev = ev.get("device", "unknown")
        ip = ev.get("vpn_ip", "—")
        peer = ev.get("peer", "—")
        mode = ev.get("mode", "quantum")
        mode_tag = f"{MAGENTA}PQC (ML-KEM-1024){RESET}" if mode == "quantum" else f"{BLUE}Standard (X25519){RESET}"
        print(f"[{time_str}] {GREEN}▶ [CONNECT]{RESET} Device: {BOLD}{dev}{RESET} | Assigned IP: {BOLD}{ip}{RESET} | Peer: {peer} | Mode: {mode_tag}")

    elif kind == "session_end":
        dev = ev.get("device", "unknown")
        ip = ev.get("vpn_ip", "—")
        dur = ev.get("duration", 0)
        b_in = format_bytes(ev.get("bytes_in", 0))
        b_out = format_bytes(ev.get("bytes_out", 0))
        dropped = ev.get("dropped", {})
        drop_str = f"Replay drops: {dropped.get('replay', 0)}, Spoof: {dropped.get('spoof', 0)}"
        print(f"[{time_str}] {RED}⏹ [DISCONNECT]{RESET} Device: {BOLD}{dev}{RESET} ({ip}) | Duration: {dur}s | In: {b_in} | Out: {b_out} | {drop_str}")

    elif kind == "flow":
        dev = ev.get("device", "—")
        direction = ev.get("direction", "out")
        proto = ev.get("proto", "IP")
        size = ev.get("size", 0)

        if direction == "out":
            dst = ev.get("dst", "—")
            dport = ev.get("dport")
            dns = ev.get("dns_query")
            if dns:
                print(f"[{time_str}] {CYAN}🔍 [DNS QUERY]{RESET}  {BOLD}{dns}{RESET} -> Resolver: {dst}:{dport} (via {dev})")
            else:
                port_label = f":{dport}" if dport else ""
                service = "HTTPS" if dport == 443 else ("HTTP" if dport == 80 else ("DNS" if dport == 53 else proto))
                print(f"[{time_str}] {DIM}↑ [FLOW OUT]{RESET}   {dev} -> {dst}{port_label} [{service}] ({size} B)")
        else:
            src = ev.get("src", "—")
            print(f"[{time_str}] {DIM}↓ [FLOW IN]{RESET}    {src} -> {dev} [{proto}] ({size} B)")

    elif kind == "auth_failed":
        peer = ev.get("peer", "—")
        reason = ev.get("reason", "Token mismatch")
        print(f"[{time_str}] {RED}{BOLD}⚠ [AUTH FAILED]{RESET} Unauthorized client connection from {peer}: {reason}")

    elif kind == "handshake_error":
        peer = ev.get("peer", "—")
        reason = ev.get("reason", "Unknown")
        print(f"[{time_str}] {YELLOW}⚠ [HANDSHAKE ERR]{RESET} Handshake aborted from {peer}: {reason}")

    else:
        print(f"[{time_str}] [{kind.upper()}] {ev}")


def tail_log():
    print_banner()
    os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "a", encoding="utf-8").close()

    print(f"[*] Monitoring live tunnel stream... Press Ctrl+C to exit.\n")

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        # Catch up with last 15 lines if existing
        lines = f.readlines()
        for line in lines[-15:]:
            render_event(line)

        # Follow file in real time
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                render_event(line)
            else:
                time.sleep(0.1)


if __name__ == "__main__":
    try:
        tail_log()
    except KeyboardInterrupt:
        print(f"\n{DIM}[*] Monitor stopped by user.{RESET}")
        sys.exit(0)
