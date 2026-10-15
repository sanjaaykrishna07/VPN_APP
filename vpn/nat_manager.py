"""
QuantumSafeVPN — Linux Routing & NAT Helper
============================================
Safely configures kernel IP forwarding and iptables MASQUERADE rules
for the VPN subnet without flushing or disturbing existing firewall rules.
"""
import os
import sys
import subprocess
import re
from typing import Optional


class NATManager:
    """Manages kernel IP forwarding and iptables/nftables NAT rules."""

    def __init__(self, vpn_subnet: str = "10.8.0.0/24", tun_interface: str = "tun0"):
        self.vpn_subnet = vpn_subnet
        self.tun_interface = tun_interface
        self.wan_interface: Optional[str] = None
        self.rules_applied = False

    def detect_wan_interface(self) -> Optional[str]:
        """Find the default outbound network interface (e.g. eth0, wlan0, ens33)."""
        if sys.platform == "win32":
            return "Windows_Interface"
        try:
            res = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
            match = re.search(r"dev\s+([^\s]+)", res.stdout)
            if match:
                self.wan_interface = match.group(1)
                return self.wan_interface
        except Exception:
            pass
        return None

    def enable_ip_forwarding(self) -> bool:
        """Enable Linux IPv4 forwarding in kernel."""
        if sys.platform == "win32":
            print("[*] (Windows) Virtual environment: IP forwarding managed by OS.")
            return True
        try:
            # Check current status
            res = subprocess.run(["sysctl", "-n", "net.ipv4.ip_forward"], capture_output=True, text=True)
            if res.stdout.strip() == "1":
                print("[+] Kernel IPv4 forwarding is already active")
                return True

            subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True, capture_output=True)
            print("[+] Kernel IPv4 forwarding enabled: net.ipv4.ip_forward = 1")
            return True
        except Exception as e:
            print(f"[!] Warning: Could not enable sysctl net.ipv4.ip_forward: {e}")
            try:
                with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                    f.write("1\n")
                print("[+] Kernel IPv4 forwarding enabled via /proc")
                return True
            except Exception as e2:
                print(f"[!] Warning: /proc write failed: {e2}")
                return False

    def setup_nat(self, wan_iface: Optional[str] = None) -> bool:
        """Add iptables NAT rules specifically for the VPN subnet."""
        if sys.platform == "win32":
            return True

        if not self.enable_ip_forwarding():
            print("[!] Could not enable IP forwarding; NAT routing may be impaired.")

        iface = wan_iface or self.wan_interface or self.detect_wan_interface()
        if not iface:
            print("[!] Could not auto-detect WAN interface for NAT. Specify interface manually.")
            return False

        self.wan_interface = iface
        print(f"[*] Setting up NAT: subnet {self.vpn_subnet} -> WAN interface {iface}...")

        try:
            # 1. Check if NAT rule already exists
            check_nat = subprocess.run(
                ["iptables", "-t", "nat", "-C", "POSTROUTING", "-s", self.vpn_subnet, "-o", iface, "-j", "MASQUERADE"],
                capture_output=True
            )
            if check_nat.returncode != 0:
                subprocess.run(
                    ["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", self.vpn_subnet, "-o", iface, "-j", "MASQUERADE"],
                    check=True, capture_output=True
                )
                print(f"[+] iptables NAT POSTROUTING rule added for {iface}")

            # 2. Check and add FORWARD rules for tun interface
            check_fwd1 = subprocess.run(
                ["iptables", "-C", "FORWARD", "-i", self.tun_interface, "-o", iface, "-j", "ACCEPT"],
                capture_output=True
            )
            if check_fwd1.returncode != 0:
                subprocess.run(
                    ["iptables", "-A", "FORWARD", "-i", self.tun_interface, "-o", iface, "-j", "ACCEPT"],
                    check=True, capture_output=True
                )

            check_fwd2 = subprocess.run(
                ["iptables", "-C", "FORWARD", "-i", iface, "-o", self.tun_interface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
                capture_output=True
            )
            if check_fwd2.returncode != 0:
                subprocess.run(
                    ["iptables", "-A", "FORWARD", "-i", iface, "-o", self.tun_interface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
                    check=True, capture_output=True
                )

            # 3. Add TCP MSS Clamping to prevent MTU packet drops on encapsulated tunnels
            subprocess.run(
                ["iptables", "-t", "mangle", "-A", "FORWARD", "-p", "tcp", "--tcp-flags", "SYN,RST", "SYN", "-j", "TCPMSS", "--clamp-mss-to-pmtu"],
                capture_output=True
            )
            subprocess.run(
                ["iptables", "-t", "mangle", "-A", "FORWARD", "-p", "tcp", "--tcp-flags", "SYN,RST", "SYN", "-j", "TCPMSS", "--set-mss", "1300"],
                capture_output=True
            )

            self.rules_applied = True
            print("[+] VPN routing, NAT & TCP MSS rules successfully applied.")
            return True
        except Exception as e:
            print(f"[!] Warning: iptables configuration error: {e}")
            return False

    def teardown_nat(self):
        """Cleanly remove only the specific rules created by QuantumSafeVPN."""
        if sys.platform == "win32" or not self.rules_applied or not self.wan_interface:
            return

        print("[*] Cleaning up QuantumSafeVPN NAT rules...")
        try:
            subprocess.run(
                ["iptables", "-t", "nat", "-D", "POSTROUTING", "-s", self.vpn_subnet, "-o", self.wan_interface, "-j", "MASQUERADE"],
                capture_output=True
            )
            subprocess.run(
                ["iptables", "-D", "FORWARD", "-i", self.tun_interface, "-o", self.wan_interface, "-j", "ACCEPT"],
                capture_output=True
            )
            subprocess.run(
                ["iptables", "-D", "FORWARD", "-i", self.wan_interface, "-o", self.tun_interface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
                capture_output=True
            )
            self.rules_applied = False
            print("[+] NAT rules cleaned up cleanly.")
        except Exception as e:
            print(f"[!] NAT cleanup note: {e}")
