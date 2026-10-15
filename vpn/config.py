"""
QuantumSafeVPN — Configuration Loader
======================================
Loads server and client configurations from YAML or environment variables.
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "server.yaml")

DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 7000,
        "tun_name": "tun0",
        "tun_network": "10.8.0.0/24",
        "server_ip": "10.8.0.1",
        "client_ip_start": "10.8.0.2",
        "client_ip_end": "10.8.0.254",
        "mtu": 1400,
        "dns_servers": ["1.1.1.1", "8.8.8.8"],
        "enable_nat": True,
        "wan_interface": "auto",
        "mode": "standalone",
    },
    "crypto": {
        "kem_algorithm": "ML-KEM-1024",
        "dsa_algorithm": "ML-DSA-65",
        "symmetric_cipher": "AES-256-GCM",
        "kdf": "HKDF-SHA256",
        "replay_window_size": 64,
    },
    "logging": {
        "level": "INFO",
        "log_file": "logs/quantumsafevpn.log",
    }
}


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file, with environment variable overrides."""
    config = dict(DEFAULT_CONFIG)
    target_path = config_path or CONFIG_FILE

    if os.path.exists(target_path):
        try:
            import yaml
            with open(target_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded and isinstance(loaded, dict):
                    for section, values in loaded.items():
                        if section in config and isinstance(values, dict):
                            config[section].update(values)
                        else:
                            config[section] = values
        except Exception:
            # Fallback simple line parser if pyyaml not installed
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("port:"):
                            config["server"]["port"] = int(line.split(":")[1].strip())
                        elif line.startswith("server_ip:"):
                            config["server"]["server_ip"] = line.split(":")[1].strip().strip('"\'')
            except Exception:
                pass

    # Environment Variable Overrides
    if "VPN_SERVER_PORT" in os.environ:
        config["server"]["port"] = int(os.environ["VPN_SERVER_PORT"])
    if "VPN_SERVER_HOST" in os.environ:
        config["server"]["host"] = os.environ["VPN_SERVER_HOST"]
    if "VPN_SERVER_IP" in os.environ:
        config["server"]["server_ip"] = os.environ["VPN_SERVER_IP"]
    if "VPN_MODE" in os.environ:
        config["server"]["mode"] = os.environ["VPN_MODE"]

    return config
