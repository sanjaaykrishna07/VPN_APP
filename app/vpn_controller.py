import subprocess
import threading
import time


class VPNController:

    def __init__(self):
        self.process = None
        self.status = "Disconnected"

    def connect(self):
        if self.process is not None:
            print("[!] VPN is already running")
            return

        print("[*] Starting QuantumSafeVPN client...")

        command = [
            "sudo",
            "ip",
            "netns",
            "exec",
            "vpn-client",
            "env",
            "PYTHONPATH=/home/kali/QuantumSafeVPN",
            "/home/kali/QuantumSafeVPN/venv/bin/python",
            "/home/kali/QuantumSafeVPN/vpn/tunnel_client.py"
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            self.status = "Connecting"

            threading.Thread(
                target=self._read_output,
                daemon=True
            ).start()

            print("[+] VPN process started")

        except Exception as e:
            self.process = None
            self.status = "Disconnected"
            print(f"[!] Failed to start VPN: {e}")

    def _read_output(self):
        if self.process is None:
            return

        for line in self.process.stdout:
            line = line.rstrip()

            if line:
                print(f"[VPN] {line}")

            if "QuantumSafeVPN client is running" in line:
                self.status = "Connected"
                print("[+] VPN connection established")

        self.status = "Disconnected"
        self.process = None

        print("[*] VPN process stopped")

    def disconnect(self):
        if self.process is None:
            print("[!] VPN is not running")
            return

        print("[*] Disconnecting VPN...")

        try:
            self.process.terminate()

            try:
                self.process.wait(timeout=5)

            except subprocess.TimeoutExpired:
                print("[!] VPN did not stop gracefully")
                self.process.kill()
                self.process.wait()

        except Exception as e:
            print(f"[!] Error stopping VPN: {e}")

        finally:
            self.process = None
            self.status = "Disconnected"

        print("[+] VPN disconnected")

    def get_status(self):
        return self.status


if __name__ == "__main__":

    vpn = VPNController()

    print("=" * 60)
    print("QuantumSafeVPN Controller Test")
    print("=" * 60)

    vpn.connect()

    try:
        while True:
            time.sleep(1)

            if vpn.get_status() == "Connected":
                print("[+] Status: CONNECTED")

    except KeyboardInterrupt:
        print()
        print("[*] Stopping VPN...")

        vpn.disconnect()

        print("[+] Controller test finished")
