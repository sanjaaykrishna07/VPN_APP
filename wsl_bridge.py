#!/usr/bin/env python3
"""
QuantumSafeVPN — High-Performance Windows-to-WSL Port 7000 Bridge
=================================================================
Binds to 0.0.0.0:7000 on Windows across all network interfaces
and pipes all connections directly into the WSL2 Linux VPN server.
"""

import socket
import threading
import sys
import time
import subprocess

def get_lan_ips():
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return ips or ["127.0.0.1"]

def get_wsl_ip():
    try:
        out = subprocess.check_output(["wsl", "hostname", "-I"], text=True)
        ips = out.strip().split()
        if ips:
            return ips[0]
    except Exception:
        pass
    return "172.20.26.243"

WSL_IP = get_wsl_ip()
PORT = 7000

def forward_stream(src, dst, name):
    bytes_count = 0
    last_log_time = time.time()
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
            bytes_count += len(data)
            now = time.time()
            if now - last_log_time >= 3.0:
                print(f"[BRIDGE] {name}: {bytes_count / 1024:.1f} KB transferred")
                sys.stdout.flush()
                last_log_time = now
    except Exception:
        pass
    finally:
        print(f"[BRIDGE] {name} closed (Total: {bytes_count / 1024:.1f} KB)")
        sys.stdout.flush()
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

def handle_client(phone_sock, phone_addr):
    phone_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"\n[+] [BRIDGE] Incoming connection from phone: {phone_addr[0]}:{phone_addr[1]}")
    sys.stdout.flush()
    try:
        wsl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        wsl_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        wsl_sock.connect((WSL_IP, PORT))
        print(f"[+] [BRIDGE] Tunneling phone ({phone_addr[0]}) -> WSL Linux Gateway ({WSL_IP}:{PORT})")
        sys.stdout.flush()
    except Exception as e:
        print(f"[!] [BRIDGE] Failed to connect to WSL ({WSL_IP}:{PORT}): {e}")
        sys.stdout.flush()
        phone_sock.close()
        return

    t1 = threading.Thread(target=forward_stream, args=(phone_sock, wsl_sock, "Phone->WSL"), daemon=True)
    t2 = threading.Thread(target=forward_stream, args=(wsl_sock, phone_sock, "WSL->Phone"), daemon=True)
    t1.start()
    t2.start()

def main():
    lan_ips = get_lan_ips()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    try:
        server.bind(("0.0.0.0", PORT))
    except Exception as e:
        print(f"[!] Could not bind to 0.0.0.0:{PORT}: {e}")
        return

    server.listen(50)
    print("=" * 65)
    print("   [+] QuantumSafeVPN Windows-to-WSL Bridge is ACTIVE!")
    print("=" * 65)
    print(f"  Windows Wi-Fi / LAN IP: {lan_ips[0]}")
    print(f"  Enter in Phone App:     Host: {lan_ips[0]}  |  Port: {PORT}")
    print(f"  Forwarding to WSL:      {WSL_IP}:{PORT}")
    print("=" * 65)
    sys.stdout.flush()

    while True:
        try:
            phone_sock, phone_addr = server.accept()
            threading.Thread(target=handle_client, args=(phone_sock, phone_addr), daemon=True).start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] Bridge error: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
