import os
import struct
import subprocess
import sys

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

TUNSETIFF = 0x400454CA
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000


class TunUnavailableError(RuntimeError):
    """Raised when a real TUN device cannot be created. The VPN refuses to
    pretend it is routing traffic when it is not."""


class TunInterface:
    """
    Real Linux TUN device.

    The previous implementation silently fell back to a "virtual" device that
    fabricated a fake packet every second, so a server could report a ready
    tunnel while forwarding nothing. That fallback is gone: if the device cannot
    be opened this raises TunUnavailableError.
    """

    def __init__(self, name="tun0", mtu=1400):
        self.name = name
        self.mtu = mtu
        self.fd = None
        self.is_virtual = False  # always False; kept so older callers don't break

    def create(self):
        if not HAS_FCNTL or sys.platform == "win32":
            raise TunUnavailableError(
                "A real TUN device needs Linux. Run the server on the Linux/AWS host "
                "(Windows is supported for the Android client only).")
        try:
            self.fd = os.open("/dev/net/tun", os.O_RDWR)
            ifr = struct.pack("16sH", self.name.encode(), IFF_TUN | IFF_NO_PI)
            result = fcntl.ioctl(self.fd, TUNSETIFF, ifr)
            self.name = result[:16].split(b"\x00", 1)[0].decode()
        except OSError as exc:
            self.fd = None
            raise TunUnavailableError(
                f"Cannot open /dev/net/tun ({exc}). Run as root (or with CAP_NET_ADMIN) "
                "on a host that provides /dev/net/tun.") from exc
        print(f"[+] TUN interface created: {self.name}")
        return self.fd

    def configure(self, address):
        """Assign the address and bring the link up. Failure is fatal."""
        try:
            subprocess.run(["ip", "addr", "replace", address, "dev", self.name], check=True)
            subprocess.run(["ip", "link", "set", self.name, "mtu", str(self.mtu), "up"], check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise TunUnavailableError(f"Could not configure {self.name} with {address}: {exc}") from exc
        print(f"[+] {self.name} configured: {address} (mtu {self.mtu})")

    def read_packet(self):
        if self.fd is None:
            raise RuntimeError("TUN interface is not created")
        return os.read(self.fd, 65535)

    def write_packet(self, packet):
        if self.fd is None:
            raise RuntimeError("TUN interface is not created")
        if packet:
            os.write(self.fd, packet)

    def close(self):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
        self.fd = None
