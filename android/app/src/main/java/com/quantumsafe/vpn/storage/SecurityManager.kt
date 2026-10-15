package com.quantumsafe.vpn.storage

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.quantumsafe.vpn.model.ServerConfig

class SecurityManager(context: Context) {

    private val prefs: SharedPreferences = try {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    } catch (_: Exception) {
        context.getSharedPreferences("${PREFS_NAME}_fallback", Context.MODE_PRIVATE)
    }

    fun getServerConfig(): ServerConfig {
        return ServerConfig(
            host = prefs.getString(KEY_HOST, "192.168.1.100") ?: "192.168.1.100",
            port = prefs.getInt(KEY_PORT, 7000),
            timeoutSeconds = prefs.getInt(KEY_TIMEOUT, 10),
            mtu = prefs.getInt(KEY_MTU, 1400),
            autoConnect = prefs.getBoolean(KEY_AUTO_CONNECT, false),
            quantumSafeMode = prefs.getBoolean(KEY_QUANTUM_SAFE, true),
            inspectionEnabled = prefs.getBoolean(KEY_INSPECTION, false),
            deviceName = prefs.getString(KEY_DEVICE_NAME, "android-phone") ?: "android-phone",
            deviceToken = prefs.getString(KEY_DEVICE_TOKEN, "7cc0af0e368d217a6fd0b2b8259abc8fead9739f43d8be76cd412414ac5d9268") ?: "7cc0af0e368d217a6fd0b2b8259abc8fead9739f43d8be76cd412414ac5d9268",
            pinnedFingerprint = prefs.getString(KEY_PINNED_FINGERPRINT, "77497277cece090a1fc6054cb9f51a9fa7e4c9353a673dc133f675c22323a0dc") ?: "77497277cece090a1fc6054cb9f51a9fa7e4c9353a673dc133f675c22323a0dc"
        )
    }

    fun saveServerConfig(config: ServerConfig) {
        prefs.edit()
            .putString(KEY_HOST, config.host)
            .putInt(KEY_PORT, config.port)
            .putInt(KEY_TIMEOUT, config.timeoutSeconds)
            .putInt(KEY_MTU, config.mtu)
            .putBoolean(KEY_AUTO_CONNECT, config.autoConnect)
            .putBoolean(KEY_QUANTUM_SAFE, config.quantumSafeMode)
            .putBoolean(KEY_INSPECTION, config.inspectionEnabled)
            .putString(KEY_DEVICE_NAME, config.deviceName)
            .putString(KEY_DEVICE_TOKEN, config.deviceToken)
            .putString(KEY_PINNED_FINGERPRINT, config.pinnedFingerprint)
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "quantumsafe_secure_prefs"
        private const val KEY_HOST = "server_host"
        private const val KEY_PORT = "server_port"
        private const val KEY_TIMEOUT = "connection_timeout"
        private const val KEY_MTU = "tunnel_mtu"
        private const val KEY_AUTO_CONNECT = "auto_connect"
        private const val KEY_QUANTUM_SAFE = "quantum_safe_mode"
        private const val KEY_INSPECTION = "inspection_enabled"
        private const val KEY_DEVICE_NAME = "device_name"
        private const val KEY_DEVICE_TOKEN = "device_token"
        private const val KEY_PINNED_FINGERPRINT = "pinned_fingerprint"
    }
}
