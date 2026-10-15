package com.quantumsafe.vpn.model

enum class VpnStatus {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    ERROR
}

data class ServerConfig(
    val host: String = "192.168.1.100",
    val port: Int = 7000,
    val timeoutSeconds: Int = 10,
    val mtu: Int = 1400,
    val autoConnect: Boolean = false,
    val quantumSafeMode: Boolean = true,
    val inspectionEnabled: Boolean = false,
    val deviceName: String = "android-phone",
    val deviceToken: String = "7cc0af0e368d217a6fd0b2b8259abc8fead9739f43d8be76cd412414ac5d9268",
    val pinnedFingerprint: String = "77497277cece090a1fc6054cb9f51a9fa7e4c9353a673dc133f675c22323a0dc"
)

data class ConnectionMetrics(
    val assignedIp: String = "—",
    val serverEndpoint: String = "—",
    val dnsServers: String = "1.1.1.1, 8.8.8.8",
    val mtu: Int = 1400,
    val durationSeconds: Long = 0L,
    val bytesIn: Long = 0L,
    val bytesOut: Long = 0L,
    val packetsIn: Long = 0L,
    val packetsOut: Long = 0L,
    val keyExchange: String = "ML-KEM-1024 (Kyber)",
    val authentication: String = "ML-DSA-65 (Dilithium)",
    val encryption: String = "AES-256-GCM"
)

data class ShorDemoResult(
    val isQuantumSafe: Boolean,
    val modulusBitLength: Int,
    val executionTimeMs: Long,
    val recoveredKeyHex: String,
    val testCiphertextHex: String,
    val decryptedPlaintext: String,
    val success: Boolean,
    val statusMessage: String,
    val mathematicalProof: String
)

data class VpnUiState(
    val status: VpnStatus = VpnStatus.DISCONNECTED,
    val statusMessage: String = "Disconnected",
    val errorMessage: String? = null,
    val serverConfig: ServerConfig = ServerConfig(),
    val metrics: ConnectionMetrics = ConnectionMetrics(),
    val logs: List<String> = emptyList(),
    val shorDemoResult: ShorDemoResult? = null,
    val isAnalyzingShor: Boolean = false
)
