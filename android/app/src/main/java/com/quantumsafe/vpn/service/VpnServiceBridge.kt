package com.quantumsafe.vpn.service

import com.quantumsafe.vpn.model.ConnectionMetrics
import com.quantumsafe.vpn.model.VpnStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object VpnServiceBridge {

    private val _status = MutableStateFlow(VpnStatus.DISCONNECTED)
    val status = _status.asStateFlow()

    private val _statusMessage = MutableStateFlow("Ready to connect")
    val statusMessage = _statusMessage.asStateFlow()

    private val _metrics = MutableStateFlow(ConnectionMetrics())
    val metrics = _metrics.asStateFlow()

    private val _logs = MutableStateFlow<List<String>>(emptyList())
    val logs = _logs.asStateFlow()

    private val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())

    fun updateStatus(newStatus: VpnStatus, message: String = "") {
        _status.value = newStatus
        _statusMessage.value = if (message.isNotBlank()) message else when (newStatus) {
            VpnStatus.DISCONNECTED -> "Disconnected"
            VpnStatus.CONNECTING -> "Connecting..."
            VpnStatus.CONNECTED -> "Connected (Post-Quantum Secure)"
            VpnStatus.ERROR -> "Connection Error"
        }
    }

    fun updateMetrics(transform: (ConnectionMetrics) -> ConnectionMetrics) {
        _metrics.value = transform(_metrics.value)
    }

    fun addLog(message: String) {
        val timestamp = timeFormat.format(Date())
        val entry = "[$timestamp] $message"
        val current = _logs.value.toMutableList()
        current.add(entry)
        if (current.size > 200) current.removeAt(0)
        _logs.value = current
    }

    fun clearLogs() {
        _logs.value = emptyList()
    }
}
