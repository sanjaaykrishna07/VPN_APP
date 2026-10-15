# QuantumSafeVPN — Ubuntu & WSL2 Setup Guide

This guide walks you through running the QuantumSafe VPN server on **Ubuntu (WSL2 / Native Linux / VM)** to enable real kernel packet tunneling (`tun0`) and `iptables` NAT forwarding.

---

## 1. Quick Access in WSL (No Copying Needed!)

In WSL2 Ubuntu, your Windows `D:\VPN_APP` drive is already mounted automatically:

```bash
cd /mnt/d/VPN_APP
```

*(Or, if you prefer running inside your Ubuntu home directory, unzip the package as shown in Section 2).*

---

## 2. Unzipping the Standalone Linux Package

If you want the project completely inside your Ubuntu Linux filesystem:

```bash
# 1. Copy the zip from Windows D: drive to your Ubuntu home folder
cp /mnt/d/VPN_APP/QuantumSafeVPN_Linux.zip ~/

# 2. Extract the archive
cd ~
sudo apt install -y unzip
unzip QuantumSafeVPN_Linux.zip
cd QuantumSafeVPN
```

---

## 3. Install System Packages & Prerequisites

Update Ubuntu packages and install required networking utilities:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv iptables net-tools iproute2
```

---

## 4. Install Python Dependencies

Set up a virtual environment and install the required cryptography and web modules:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Enable Kernel Forwarding & NAT (One-Click)

Run the automated provisioning script as root:

```bash
sudo bash deploy/setup_server.sh
```

This script:
1. Enables Linux kernel IPv4 forwarding (`net.ipv4.ip_forward = 1`).
2. Detects your physical WAN interface (`eth0` / `wlan0`).
3. Configures `iptables` MASQUERADE for the VPN subnet `10.8.0.0/24`.

---

## 6. Start the QuantumSafe VPN Server

Run the VPN daemon with root privileges (required for `/dev/net/tun`):

```bash
# Option A: Standalone Post-Quantum Tunnel Server (Port 7000)
sudo venv/bin/python vpn/tunnel_server.py

# Option B: Web Dashboard + VPN Controller (Port 8000)
sudo venv/bin/python run.py --port 8000
```

---

## 7. Connecting Your Android Phone

1. Find your Linux machine's IP address:
   ```bash
   hostname -I | awk '{print $1}'
   ```
2. Open the **QuantumSafe VPN** app on your Android device.
3. In **Server Configuration**, enter this IP address and Port `7000`.
4. Tap **Connect**.

> **Note for WSL2 Users:**  
> If your phone is on Wi-Fi and connecting to your laptop running WSL2, forward port 7000 from Windows to WSL2 by running this command in **Windows PowerShell (as Administrator)**:
> ```powershell
> netsh interface portproxy add v4tov4 listenport=7000 listenaddress=0.0.0.0 connectport=7000 connectaddress=<YOUR_WSL_IP>
> ```
