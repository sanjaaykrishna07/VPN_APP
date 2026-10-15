package com.quantumsafe.vpn

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.quantumsafe.vpn.model.VpnStatus
import com.quantumsafe.vpn.service.VpnServiceBridge
import com.quantumsafe.vpn.storage.SecurityManager
import com.quantumsafe.vpn.ui.MainScreen
import com.quantumsafe.vpn.ui.theme.QuantumSafeTheme
import com.quantumsafe.vpn.ui.theme.WhiteBackground
import com.quantumsafe.vpn.viewmodel.VpnViewModel

class MainActivity : ComponentActivity() {

    private lateinit var securityManager: SecurityManager
    private lateinit var viewModel: VpnViewModel

    private val vpnConsentLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            VpnServiceBridge.addLog("[+] VPN system consent granted by user")
            viewModel.startVpn(this)
        } else {
            VpnServiceBridge.addLog("[!] VPN system consent was denied by user")
            VpnServiceBridge.updateStatus(VpnStatus.ERROR, "VPN permission denied")
        }
    }

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { _ ->
        // Continue regardless; foreground service notification will be attempted
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        securityManager = SecurityManager(applicationContext)
        viewModel = VpnViewModel(securityManager)

        checkNotificationPermission()

        setContent {
            QuantumSafeTheme {
                val state by viewModel.uiState.collectAsState()

                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = WhiteBackground
                ) {
                    MainScreen(
                        state = state,
                        onToggleVpn = { handleToggleVpn(state.status) },
                        onSetQuantumSafeMode = { viewModel.setQuantumSafeMode(it) },
                        onSetInspectionEnabled = { viewModel.setInspectionEnabled(it) },
                        onRunShorDemonstration = { viewModel.runShorDemonstration() },
                        onSaveConfig = { host, port, timeout, mtu, autoConnect, dev, tok, pin ->
                            viewModel.updateConfig(host, port, timeout, mtu, autoConnect, dev, tok, pin)
                        },
                        onClearLogs = { viewModel.clearLogs() }
                    )
                }
            }
        }

        // Handle auto-connect if enabled
        val config = securityManager.getServerConfig()
        if (config.autoConnect && VpnServiceBridge.status.value == VpnStatus.DISCONNECTED) {
            handleToggleVpn(VpnStatus.DISCONNECTED)
        }
    }

    private fun handleToggleVpn(currentStatus: VpnStatus) {
        if (currentStatus == VpnStatus.CONNECTED || currentStatus == VpnStatus.CONNECTING) {
            viewModel.stopVpn(this)
        } else {
            val prepareIntent = VpnService.prepare(this)
            if (prepareIntent != null) {
                // System consent required
                vpnConsentLauncher.launch(prepareIntent)
            } else {
                // Consent already granted
                viewModel.startVpn(this)
            }
        }
    }

    private fun checkNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }
}
