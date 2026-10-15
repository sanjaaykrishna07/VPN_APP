# QuantumSafeVPN — Troubleshooting & Diagnostic Guide

This guide covers common network, cryptographic, and OS-specific issues encountered during deployment.

---

## 1. Connection & Network Diagnostics

### Issue: Android client shows `Connection refused` or `Connection timed out`
- **Cause**: Linux server is not running, port 7000 is blocked by a host firewall, or the IP address entered on the phone is incorrect.
- **Remedy**:
  1. Verify the server is listening: `ss -tulpn | grep 7000`.
  2. Allow port 7000 in UFW/firewalld: `sudo ufw allow 7000/tcp`.
  3. Ensure both phone and server are on the same Wi-Fi subnet (e.g. `11.12.x.x`). Ping the server from the phone's Wi-Fi network.

### Issue: Android connects, but websites do not load (No Internet)
- **Cause**: Linux kernel IPv4 forwarding is disabled, or iptables MASQUERADE was configured with the wrong WAN interface.
- **Remedy**:
  1. Check forwarding: `sysctl net.ipv4.ip_forward` (must be `1`).
  2. Check outbound WAN interface: `ip route show default`.
  3. Run `sudo bash scripts/setup_network.sh` to ensure NAT rules are applied.

---

## 2. Cryptographic Diagnostics

### Issue: `ML-DSA-65 signature verification failed`
- **Cause**: Transcript mismatch between client and server or corrupted signature payload.
- **Remedy**: Ensure both client and server are running the latest codebase where transcript format is `b"QuantumSafeVPN-v1" + client_kem_pk + ciphertext`.

### Issue: `AES-GCM authentication tag mismatch`
- **Cause**: Corrupted packet in transit, key derivation mismatch, or packet tampering.
- **Remedy**: Check that both sides derived the session key using identical HKDF salt (`0x00*32`) and info (`b"QuantumSafeVPN-Session-Key"`).

---

## 3. Useful Diagnostic Commands

```bash
# Check active TUN device
ip addr show tun0

# Check kernel IP forwarding
sysctl net.ipv4.ip_forward

# Inspect active iptables NAT rules
sudo iptables -t nat -L POSTROUTING -v -n

# Real-time packet capture on VPN tunnel
sudo tcpdump -i tun0 -n -vv

# Check server logs in real time
tail -f logs/quantumsafevpn.log
```
