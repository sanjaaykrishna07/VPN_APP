from tun import TunInterface


def main():

    tun = TunInterface("tun0")

    try:
        tun.create()

        print(
            f"[+] Waiting for packets on {tun.name}..."
        )

        while True:
            packet = tun.read_packet()

            print(
                f"[+] Received packet: "
                f"{len(packet)} bytes"
            )

            print(
                packet[:32].hex()
            )

    except KeyboardInterrupt:

        print("\n[*] Stopping TUN test")

    finally:

        tun.close()


if __name__ == "__main__":
    main()
