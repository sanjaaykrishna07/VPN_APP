package com.quantumsafe.vpn.viewmodel

import android.content.Context
import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quantumsafe.vpn.QuantumSafeVpnService
import com.quantumsafe.vpn.crypto.PqcEngine
import com.quantumsafe.vpn.model.ServerConfig
import com.quantumsafe.vpn.model.ShorDemoResult
import com.quantumsafe.vpn.model.VpnStatus
import com.quantumsafe.vpn.model.VpnUiState
import com.quantumsafe.vpn.service.VpnServiceBridge
import com.quantumsafe.vpn.storage.SecurityManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class VpnViewModel(private val securityManager: SecurityManager) : ViewModel() {

    private val _serverConfig = MutableStateFlow(securityManager.getServerConfig())
    private val _shorResult = MutableStateFlow<ShorDemoResult?>(null)
    private val _isAnalyzingShor = MutableStateFlow(false)

    private var timerJob: Job? = null
    private var connectionStartTime = 0L

    private val serviceFlow = combine(
        VpnServiceBridge.status,
        VpnServiceBridge.statusMessage,
        VpnServiceBridge.metrics,
        VpnServiceBridge.logs
    ) { status, statusMessage, metrics, logs ->
        ServiceSnapshot(status, statusMessage, metrics, logs)
    }

    private val labFlow = combine(
        _serverConfig,
        _shorResult,
        _isAnalyzingShor
    ) { config, shorResult, isAnalyzing ->
        LabSnapshot(config, shorResult, isAnalyzing)
    }

    val uiState = combine(serviceFlow, labFlow) { s, l ->
        VpnUiState(
            status = s.status,
            statusMessage = s.statusMessage,
            serverConfig = l.config,
            metrics = s.metrics,
            logs = s.logs,
            shorDemoResult = l.shorResult,
            isAnalyzingShor = l.isAnalyzing
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = VpnUiState(serverConfig = securityManager.getServerConfig())
    )

    init {
        viewModelScope.launch {
            VpnServiceBridge.status.collect { status ->
                when (status) {
                    VpnStatus.CONNECTED -> startDurationTimer()
                    else -> stopDurationTimer()
                }
            }
        }
    }

    private fun startDurationTimer() {
        timerJob?.cancel()
        connectionStartTime = System.currentTimeMillis()
        timerJob = viewModelScope.launch {
            while (true) {
                delay(1000)
                val duration = (System.currentTimeMillis() - connectionStartTime) / 1000
                VpnServiceBridge.updateMetrics { it.copy(durationSeconds = duration) }
            }
        }
    }

    private fun stopDurationTimer() {
        timerJob?.cancel()
        timerJob = null
        VpnServiceBridge.updateMetrics { it.copy(durationSeconds = 0L) }
    }

    fun setQuantumSafeMode(enabled: Boolean) {
        val updated = _serverConfig.value.copy(quantumSafeMode = enabled)
        securityManager.saveServerConfig(updated)
        _serverConfig.value = updated
        VpnServiceBridge.addLog("[*] Cryptographic mode set to: ${if (enabled) "Quantum-Safe (ML-KEM-1024)" else "Standard (X25519)"}")
        // Re-run Shor demo analysis if one was already displayed
        if (_shorResult.value != null) {
            runShorDemonstration()
        }
    }

    fun setInspectionEnabled(enabled: Boolean) {
        val updated = _serverConfig.value.copy(inspectionEnabled = enabled)
        securityManager.saveServerConfig(updated)
        _serverConfig.value = updated
        VpnServiceBridge.addLog("[*] Network Inspection: ${if (enabled) "ON (Diagnostic telemetry active)" else "OFF (Operational logging only)"}")
    }

    fun runShorDemonstration() {
        viewModelScope.launch(Dispatchers.Default) {
            _isAnalyzingShor.value = true
            delay(300) // Brief UI feedback
            val isQuantum = _serverConfig.value.quantumSafeMode
            val result = PqcEngine.runShorDemonstration(isQuantum)
            _shorResult.value = result
            _isAnalyzingShor.value = false
            VpnServiceBridge.addLog("[LAB] Shor's Test: ${result.statusMessage}")
        }
    }

    fun updateConfig(
        host: String,
        portStr: String,
        timeoutStr: String,
        mtuStr: String,
        autoConnect: Boolean,
        deviceName: String,
        deviceToken: String,
        pinnedFingerprint: String
    ): String? {
        val trimmedHost = host.trim()
        if (trimmedHost.isBlank()) return "Server address cannot be empty"

        val port = portStr.trim().toIntOrNull()
        if (port == null || port !in 1..65535) return "Port must be a number between 1 and 65535"

        val timeout = timeoutStr.trim().toIntOrNull() ?: 10
        if (timeout !in 2..60) return "Timeout must be between 2 and 60 seconds"

        val mtu = mtuStr.trim().toIntOrNull() ?: 1400
        if (mtu !in 576..1500) return "MTU must be between 576 and 1500 bytes"

        val current = _serverConfig.value
        val newConfig = current.copy(
            host = trimmedHost,
            port = port,
            timeoutSeconds = timeout,
            mtu = mtu,
            autoConnect = autoConnect,
            deviceName = deviceName.trim().ifEmpty { "android-phone" },
            deviceToken = deviceToken.trim(),
            pinnedFingerprint = pinnedFingerprint.trim()
        )
        securityManager.saveServerConfig(newConfig)
        _serverConfig.value = newConfig
        return null
    }

    fun startVpn(context: Context) {
        val config = _serverConfig.value
        val intent = Intent(context, QuantumSafeVpnService::class.java).apply {
            action = QuantumSafeVpnService.ACTION_CONNECT
            putExtra(QuantumSafeVpnService.EXTRA_SERVER_HOST, config.host)
            putExtra(QuantumSafeVpnService.EXTRA_SERVER_PORT, config.port)
            putExtra(QuantumSafeVpnService.EXTRA_TIMEOUT_SEC, config.timeoutSeconds)
            putExtra(QuantumSafeVpnService.EXTRA_MTU, config.mtu)
            putExtra(QuantumSafeVpnService.EXTRA_QUANTUM_SAFE_MODE, config.quantumSafeMode)
            putExtra(QuantumSafeVpnService.EXTRA_INSPECTION_ENABLED, config.inspectionEnabled)
            putExtra(QuantumSafeVpnService.EXTRA_DEVICE_NAME, config.deviceName)
            putExtra(QuantumSafeVpnService.EXTRA_DEVICE_TOKEN, config.deviceToken)
            putExtra(QuantumSafeVpnService.EXTRA_PINNED_FINGERPRINT, config.pinnedFingerprint)
        }
        context.startService(intent)
    }

    fun stopVpn(context: Context) {
        val intent = Intent(context, QuantumSafeVpnService::class.java).apply {
            action = QuantumSafeVpnService.ACTION_DISCONNECT
        }
        context.startService(intent)
    }

    fun clearLogs() {
        VpnServiceBridge.clearLogs()
    }
}

private data class ServiceSnapshot(
    val status: VpnStatus,
    val statusMessage: String,
    val metrics: com.quantumsafe.vpn.model.ConnectionMetrics,
    val logs: List<String>
)

private data class LabSnapshot(
    val config: ServerConfig,
    val shorResult: ShorDemoResult?,
    val isAnalyzing: Boolean
)

