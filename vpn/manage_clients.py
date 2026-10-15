"""
Enroll / list / remove VPN devices.

    python -m vpn.manage_clients add phone-1      # prints the token ONCE
    python -m vpn.manage_clients list
    python -m vpn.manage_clients remove phone-1

The token is shown a single time and only a salted hash is stored. Put it in the
phone app (stored in Android Keystore-backed storage), never in the repository.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pqc.mldsa import KEY_DIR, load_or_create_server_identity  # noqa: E402
from vpn.handshake import ClientStore, fingerprint  # noqa: E402


def main(argv):
    path = os.environ.get("VPN_CLIENTS_FILE", os.path.join(KEY_DIR, "clients.json"))
    store = ClientStore(path)
    if len(argv) < 2 or argv[1] not in {"add", "list", "remove"}:
        print(__doc__)
        return 1
    if argv[1] == "list":
        for name in store._load():
            print(name)
        return 0
    if len(argv) < 3:
        print("device name required")
        return 1
    name = argv[2]
    if argv[1] == "add":
        pub, _ = load_or_create_server_identity()
        token = store.add_device(name)
        print(f"Device       : {name}")
        print(f"Token (ONCE) : {token}")
        print(f"Server pin   : {fingerprint(pub)}   (SHA-256 of ML-DSA-65 public key)")
        print(f"Public key   : {os.path.join(KEY_DIR, 'server_mldsa65_public.key')}  (give to the client for pinning)")
    else:
        records = store._load()
        if records.pop(name, None) is None:
            print("no such device")
            return 1
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        print(f"removed {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
