package com.quantumsafe.vpn

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import android.util.Log
import androidx.core.app.NotificationCompat
import com.quantumsafe.vpn.crypto.PqcEngine
import com.quantumsafe.vpn.model.VpnStatus
import com.quantumsafe.vpn.service.VpnServiceBridge
import org.json.JSONObject
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean

class QuantumSafeVpnService : VpnService() {

    companion object {
        const val TAG = "QuantumSafeVPN"
        const val ACTION_CONNECT = "com.quantumsafe.vpn.CONNECT"
        const val ACTION_DISCONNECT = "com.quantumsafe.vpn.DISCONNECT"

        const val EXTRA_SERVER_HOST = "SERVER_HOST"
        const val EXTRA_SERVER_PORT = "SERVER_PORT"
        const val EXTRA_TIMEOUT_SEC = "TIMEOUT_SEC"
        const val EXTRA_MTU = "MTU"
        const val EXTRA_QUANTUM_SAFE_MODE = "QUANTUM_SAFE_MODE"
        const val EXTRA_INSPECTION_ENABLED = "INSPECTION_ENABLED"
        const val EXTRA_DEVICE_NAME = "DEVICE_NAME"
        const val EXTRA_DEVICE_TOKEN = "DEVICE_TOKEN"
        const val EXTRA_PINNED_FINGERPRINT = "PINNED_FINGERPRINT"

        const val NOTIFICATION_CHANNEL_ID = "quantumsafe_vpn_channel"
        const val NOTIFICATION_ID = 101

        val isRunning = AtomicBoolean(false)
    }

    private var vpnInterface: ParcelFileDescriptor? = null
    private var vpnSocket: Socket? = null
    private var vpnThread: Thread? = null
    private val isStopping = AtomicBoolean(false)

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        if (action == ACTION_DISCONNECT) {
            disconnectVpn("User requested disconnection")
            return START_NOT_STICKY
        }

        val host = intent?.getStringExtra(EXTRA_SERVER_HOST) ?: "192.168.1.100"
        val port = intent?.getIntExtra(EXTRA_SERVER_PORT, 7000) ?: 7000
        val timeoutSec = intent?.getIntExtra(EXTRA_TIMEOUT_SEC, 10) ?: 10
        val mtu = intent?.getIntExtra(EXTRA_MTU, 1400) ?: 1400
        val quantumSafeMode = intent?.getBooleanExtra(EXTRA_QUANTUM_SAFE_MODE, true) ?: true
        val inspectionEnabled = intent?.getBooleanExtra(EXTRA_INSPECTION_ENABLED, false) ?: false
        val deviceName = intent?.getStringExtra(EXTRA_DEVICE_NAME) ?: "android-phone"
        val deviceToken = intent?.getStringExtra(EXTRA_DEVICE_TOKEN) ?: "7cc0af0e368d217a6fd0b2b8259abc8fead9739f43d8be76cd412414ac5d9268"
        val pinnedFingerprint = intent?.getStringExtra(EXTRA_PINNED_FINGERPRINT) ?: ""

        startForeground(NOTIFICATION_ID, buildNotification("Connecting to $host:$port..."))
        connectVpn(
            host = host,
            port = port,
            timeoutSec = timeoutSec,
            requestedMtu = mtu,
            quantumSafeMode = quantumSafeMode,
            inspectionEnabled = inspectionEnabled,
            deviceName = deviceName,
            deviceToken = deviceToken,
            pinnedFingerprint = pinnedFingerprint
        )
        return START_NOT_STICKY
    }

    private fun log(msg: String) {
        Log.i(TAG, msg)
        VpnServiceBridge.addLog(msg)
    }

    private fun connectVpn(
        host: String,
        port: Int,
        timeoutSec: Int,
        requestedMtu: Int,
        quantumSafeMode: Boolean,
        inspectionEnabled: Boolean,
        deviceName: String,
        deviceToken: String,
        pinnedFingerprint: String
    ) {
        if (isRunning.get()) return
        isStopping.set(false)

        vpnThread = Thread {
            try {
                isRunning.set(true)
                VpnServiceBridge.updateStatus(VpnStatus.CONNECTING, "Connecting to $host:$port...")
                val modeLabel = if (quantumSafeMode) "Quantum-Safe (ML-KEM-1024)" else "Standard (X25519)"
                log("[*] Establishing TCP connection to $host:$port ($modeLabel)...")

                val socket = Socket()
                socket.tcpNoDelay = true
                socket.keepAlive = true
                protect(socket)
                socket.connect(InetSocketAddress(host, port), timeoutSec * 1000)
                protect(socket)
                vpnSocket = socket

                val input = socket.getInputStream()
                val output = socket.getOutputStream()
                log("[+] TCP connection established with QuantumSafeVPN Server.")

                // ================= PROTOCOL v2 HANDSHAKE =================
                // 1. Client sends HELLO with mode byte ('Q' or 'S')
                val modeByte = if (quantumSafeMode) byteArrayOf('Q'.code.toByte()) else byteArrayOf('S'.code.toByte())
                val helloFrame = PqcEngine.HELLO_MAGIC + modeByte
                PqcEngine.sendFrame(output, helloFrame)
                log("[*] Transmitted Protocol v2 Hello (Mode: ${if (quantumSafeMode) "Q [ML-KEM]" else "S [X25519]"})")

                // 2. Server sends ML-DSA-65 public key (1952 bytes)
                val serverDsaPk = PqcEngine.recvFrame(input)
                if (serverDsaPk.size != PqcEngine.MLDSA_PUBLIC_KEY_SIZE) {
                    throw IllegalArgumentException("Invalid server ML-DSA identity key length: ${serverDsaPk.size} bytes")
                }
                val mdSha256 = MessageDigest.getInstance("SHA-256")
                @OptIn(ExperimentalStdlibApi::class)
                val serverFingerprint = mdSha256.digest(serverDsaPk).toHexString()
                log("[+] Server ML-DSA-65 identity received (${serverDsaPk.size}B)")
                log("[*] Server SHA-256 Key Fingerprint: $serverFingerprint")

                if (pinnedFingerprint.isNotBlank() && !serverFingerprint.equals(pinnedFingerprint.trim(), ignoreCase = true)) {
                    throw SecurityException("Server public key does not match pinned fingerprint! Aborting connection.")
                }

                // 3. Ephemeral Key Exchange
                var kemKeys: PqcEngine.KemKeyPair? = null
                var xKeys: PqcEngine.X25519KeyPair? = null
                val clientPk: ByteArray

                if (quantumSafeMode) {
                    kemKeys = PqcEngine.generateKemKeyPair()
                    clientPk = kemKeys.publicKey
                    log("[+] Generated ephemeral ML-KEM-1024 keypair (${clientPk.size}B)")
                } else {
                    xKeys = PqcEngine.generateX25519KeyPair()
                    clientPk = xKeys.publicKey
                    log("[+] Generated ephemeral X25519 keypair (${clientPk.size}B)")
                }
                PqcEngine.sendFrame(output, clientPk)

                // 4. Server sends server_part + signature
                val serverPart = PqcEngine.recvFrame(input)
                val signature = PqcEngine.recvFrame(input)
                log("[+] Received server key exchange component (${serverPart.size}B) and signature (${signature.size}B)")

                // 5. Verify Transcript Signature
                val transcript = PqcEngine.PROTOCOL_VERSION + modeByte + clientPk + serverPart
                if (!PqcEngine.verifyDsaSignature(serverDsaPk, transcript, signature)) {
                    throw SecurityException("ML-DSA-65 transcript signature verification failed! Possible MITM attack.")
                }
                log("[✓] Server ML-DSA-65 digital signature verified. Gateway authentic.")

                // 6. Decapsulate / Compute Shared Secret
                val sharedSecret = if (quantumSafeMode) {
                    PqcEngine.decapsulateKem(kemKeys!!.secretKey, serverPart)
                } else {
                    PqcEngine.computeX25519SharedSecret(xKeys!!.privateKey, serverPart)
                }

                // 7. Derive Directional Keys
                val (kC2s, kS2c) = PqcEngine.deriveDirectionalKeys(sharedSecret, transcript)
                log("[+] Derived transcript-bound directional session keys (k_c2s, k_s2c)")

                // 8. Send Encrypted Client Device Authentication
                val authObj = JSONObject().apply {
                    put("device", deviceName)
                    put("token", deviceToken)
                }
                val authCipher = PqcEngine.encryptAesGcm(kC2s, authObj.toString().toByteArray(Charsets.UTF_8), 0L)
                PqcEngine.sendFrame(output, authCipher)
                log("[*] Transmitted encrypted device credentials for '$deviceName'...")

                // 9. Receive Encrypted Lease Configuration
                val configCipher = PqcEngine.recvFrame(input)
                val (_, configBytes) = PqcEngine.decryptAesGcm(kS2c, configCipher)
                val configJson = JSONObject(String(configBytes, Charsets.UTF_8))

                val assignedIp = configJson.optString("assigned_ip", "10.8.0.2")
                val serverIp = configJson.optString("server_ip", "10.8.0.1")
                val tunMtu = configJson.optInt("mtu", requestedMtu)
                val dnsList = configJson.optJSONArray("dns")
                val dnsServers = mutableListOf<String>()
                if (dnsList != null) {
                    for (i in 0 until dnsList.length()) {
                        dnsServers.add(dnsList.getString(i))
                    }
                }
                if (dnsServers.isEmpty()) {
                    dnsServers.add("1.1.1.1")
                    dnsServers.add("8.8.8.8")
                }
                log("[✓] Lease granted: $assignedIp/24 (Gateway: $serverIp, MTU: $tunMtu)")

                // ================= CONFIGURE TUN INTERFACE =================
                val builder = Builder()
                    .setSession("QuantumSafe VPN")
                    .addAddress(assignedIp, 24)
                    .addRoute("0.0.0.0", 0)
                    .setMtu(tunMtu)
                    .setBlocking(true)

                // Prevent VPN loop by excluding own package
                try {
                    builder.addDisallowedApplication(packageName)
                } catch (_: Exception) {}

                // Capture IPv6 to avoid leakage
                try {
                    builder.addAddress("fd00:8::2", 128)
                    builder.addRoute("::", 0)
                } catch (_: Exception) {}

                for (dns in dnsServers) {
                    builder.addDnsServer(dns)
                }

                val pfd = builder.establish()
                    ?: throw IllegalStateException("Cannot create VpnService TUN interface (system consent revoked?)")
                vpnInterface = pfd

                VpnServiceBridge.updateStatus(VpnStatus.CONNECTED, "Connected: $assignedIp")
                VpnServiceBridge.updateMetrics {
                    it.copy(
                        assignedIp = assignedIp,
                        serverEndpoint = "$host:$port",
                        dnsServers = dnsServers.joinToString(", "),
                        mtu = tunMtu,
                        keyExchange = if (quantumSafeMode) "ML-KEM-1024 (Kyber)" else "X25519 (Classical)",
                        authentication = "ML-DSA-65 (Dilithium)",
                        encryption = "AES-256-GCM"
                    )
                }

                updateNotification("Connected: $assignedIp • ${if (quantumSafeMode) "Post-Quantum Secure" else "Standard Secure"}")
                log("[✓] Full tunnel established. All IP packets securely routed via AWS Gateway.")

                val tunIn = FileInputStream(pfd.fileDescriptor)
                val tunOut = FileOutputStream(pfd.fileDescriptor)

                // Worker 1: Outbound (TUN -> AES-GCM[k_c2s] -> TCP)
                val outThread = Thread {
                    val buffer = ByteArray(32767)
                    var sendSeq = 0L
                    try {
                        while (!isStopping.get() && isRunning.get()) {
                            val length = tunIn.read(buffer)
                            if (length < 0) break
                            if (length > 0) {
                                sendSeq++
                                val rawPacket = buffer.copyOfRange(0, length)
                                val encrypted = PqcEngine.encryptAesGcm(kC2s, rawPacket, sendSeq)
                                synchronized(output) {
                                    PqcEngine.sendFrame(output, encrypted)
                                }
                                VpnServiceBridge.updateMetrics { m ->
                                    m.copy(
                                        bytesOut = m.bytesOut + encrypted.size,
                                        packetsOut = m.packetsOut + 1
                                    )
                                }
                            }
                        }
                    } catch (e: Exception) {
                        if (!isStopping.get()) {
                            val msg = "Outbound tunnel closed: ${e.message ?: "EOF"}"
                            log("[!] $msg")
                            disconnectVpn(msg)
                        }
                    }
                }

                // Worker 2: Inbound (TCP -> AES-GCM[k_s2c] -> TUN)
                val inThread = Thread {
                    var lastRecvSeq = 0L
                    try {
                        while (!isStopping.get() && isRunning.get()) {
                            val encrypted = PqcEngine.recvFrame(input)
                            val (seq, rawPacket) = PqcEngine.decryptAesGcm(kS2c, encrypted)
                            if (seq <= lastRecvSeq) {
                                log("[!] Replay dropped: packet seq $seq <= last seen $lastRecvSeq")
                                continue
                            }
                            lastRecvSeq = seq
                            tunOut.write(rawPacket)
                            tunOut.flush()
                            VpnServiceBridge.updateMetrics { m ->
                                m.copy(
                                    bytesIn = m.bytesIn + encrypted.size,
                                    packetsIn = m.packetsIn + 1
                                )
                            }
                        }
                    } catch (e: Exception) {
                        if (!isStopping.get()) {
                            val msg = "Inbound tunnel closed: ${e.message ?: "EOF"}"
                            log("[!] $msg")
                            disconnectVpn(msg)
                        }
                    }
                }

                outThread.start()
                inThread.start()
                outThread.join()
                inThread.join()

            } catch (e: Exception) {
                log("[!] VPN Error: ${e.message}")
                VpnServiceBridge.updateStatus(VpnStatus.ERROR, e.message ?: "Connection failure")
            } finally {
                cleanup()
            }
        }
        vpnThread?.start()
    }

    private fun disconnectVpn(reason: String) {
        if (isStopping.getAndSet(true)) return
        log("[-] Disconnecting VPN ($reason)...")
        cleanup()
    }

    private fun cleanup() {
        isRunning.set(false)
        if (VpnServiceBridge.status.value != VpnStatus.ERROR) {
            VpnServiceBridge.updateStatus(VpnStatus.DISCONNECTED, "Disconnected")
        }
        try { vpnSocket?.close() } catch (_: Exception) {}
        try { vpnInterface?.close() } catch (_: Exception) {}
        vpnSocket = null
        vpnInterface = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
        log("[-] QuantumSafe VPN resources released.")
    }

    private fun buildNotification(text: String): Notification {
        createNotificationChannel()
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("QuantumSafe VPN")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_vpn_app)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun updateNotification(text: String) {
        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, buildNotification(text))
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "QuantumSafe VPN Tunnel Status",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows real-time tunnel state for active QuantumSafe VPN sessions"
            }
            val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        disconnectVpn("Service destroyed")
        super.onDestroy()
    }
}
