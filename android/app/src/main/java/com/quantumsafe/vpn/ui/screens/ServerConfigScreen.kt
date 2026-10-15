package com.quantumsafe.vpn.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quantumsafe.vpn.model.ServerConfig
import com.quantumsafe.vpn.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ServerConfigScreen(
    currentConfig: ServerConfig,
    onSaveConfig: (String, String, String, String, Boolean, String, String, String) -> String?,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    var host by remember { mutableStateOf(currentConfig.host) }
    var port by remember { mutableStateOf(currentConfig.port.toString()) }
    var timeout by remember { mutableStateOf(currentConfig.timeoutSeconds.toString()) }
    var mtu by remember { mutableStateOf(currentConfig.mtu.toString()) }
    var autoConnect by remember { mutableStateOf(currentConfig.autoConnect) }
    var deviceName by remember { mutableStateOf(currentConfig.deviceName) }
    var deviceToken by remember { mutableStateOf(currentConfig.deviceToken) }
    var pinnedFingerprint by remember { mutableStateOf(currentConfig.pinnedFingerprint) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var successSaved by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Server Configuration",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = CharcoalPrimary
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Outlined.ArrowBack,
                            contentDescription = "Back",
                            tint = CharcoalPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = WhiteBackground)
            )
        },
        containerColor = WhiteBackground,
        modifier = modifier
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "Specify the QuantumSafe VPN server gateway and authentication credentials. All parameters are stored encrypted via Android Keystore.",
                fontSize = 13.sp,
                color = CharcoalSecondary,
                lineHeight = 18.sp
            )

            // Server Address
            OutlinedTextField(
                value = host,
                onValueChange = {
                    host = it
                    errorMessage = null
                    successSaved = false
                },
                label = { Text("Server Host / AWS Endpoint IP") },
                placeholder = { Text("e.g. 54.x.x.x or 192.168.1.100") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = SubtleBlue,
                    unfocusedBorderColor = BorderLight,
                    focusedLabelColor = SubtleBlue,
                    unfocusedLabelColor = CharcoalMuted
                ),
                shape = RoundedCornerShape(12.dp)
            )

            // Port
            OutlinedTextField(
                value = port,
                onValueChange = {
                    port = it
                    errorMessage = null
                    successSaved = false
                },
                label = { Text("Server Port") },
                placeholder = { Text("7000 (default) or 443") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = SubtleBlue,
                    unfocusedBorderColor = BorderLight,
                    focusedLabelColor = SubtleBlue,
                    unfocusedLabelColor = CharcoalMuted
                ),
                shape = RoundedCornerShape(12.dp)
            )

            // Device Name
            OutlinedTextField(
                value = deviceName,
                onValueChange = {
                    deviceName = it
                    errorMessage = null
                    successSaved = false
                },
                label = { Text("Enrolled Device Identifier") },
                placeholder = { Text("e.g. android-phone") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = SubtleBlue,
                    unfocusedBorderColor = BorderLight,
                    focusedLabelColor = SubtleBlue,
                    unfocusedLabelColor = CharcoalMuted
                ),
                shape = RoundedCornerShape(12.dp)
            )

            // Device Token
            OutlinedTextField(
                value = deviceToken,
                onValueChange = {
                    deviceToken = it
                    errorMessage = null
                    successSaved = false
                },
                label = { Text("Enrolled Device Secret Token") },
                placeholder = { Text("64-character hex token") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = SubtleBlue,
                    unfocusedBorderColor = BorderLight,
                    focusedLabelColor = SubtleBlue,
                    unfocusedLabelColor = CharcoalMuted
                ),
                shape = RoundedCornerShape(12.dp)
            )

            // Pinned Fingerprint
            OutlinedTextField(
                value = pinnedFingerprint,
                onValueChange = {
                    pinnedFingerprint = it
                    errorMessage = null
                    successSaved = false
                },
                label = { Text("Pinned Server ML-DSA-65 Fingerprint") },
                placeholder = { Text("SHA-256 fingerprint (leave blank to accept first)") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = SubtleBlue,
                    unfocusedBorderColor = BorderLight,
                    focusedLabelColor = SubtleBlue,
                    unfocusedLabelColor = CharcoalMuted
                ),
                shape = RoundedCornerShape(12.dp)
            )

            // Network MTU & Timeout Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                OutlinedTextField(
                    value = mtu,
                    onValueChange = {
                        mtu = it
                        errorMessage = null
                        successSaved = false
                    },
                    label = { Text("Tunnel MTU") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = SubtleBlue,
                        unfocusedBorderColor = BorderLight,
                        focusedLabelColor = SubtleBlue,
                        unfocusedLabelColor = CharcoalMuted
                    ),
                    shape = RoundedCornerShape(12.dp)
                )

                OutlinedTextField(
                    value = timeout,
                    onValueChange = {
                        timeout = it
                        errorMessage = null
                        successSaved = false
                    },
                    label = { Text("Timeout (sec)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = SubtleBlue,
                        unfocusedBorderColor = BorderLight,
                        focusedLabelColor = SubtleBlue,
                        unfocusedLabelColor = CharcoalMuted
                    ),
                    shape = RoundedCornerShape(12.dp)
                )
            }

            // Auto Connect Toggle Card
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = SurfaceCard),
                border = BorderStroke(1.dp, BorderLight),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Auto-Connect",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Medium,
                            color = CharcoalPrimary
                        )
                        Text(
                            text = "Establish tunnel automatically upon application launch",
                            fontSize = 12.sp,
                            color = CharcoalMuted
                        )
                    }
                    Switch(
                        checked = autoConnect,
                        onCheckedChange = {
                            autoConnect = it
                            successSaved = false
                        },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color.White,
                            checkedTrackColor = SubtleBlue,
                            uncheckedThumbColor = CharcoalMuted,
                            uncheckedTrackColor = SurfaceVariant
                        )
                    )
                }
            }

            // Error or Success Banner
            if (errorMessage != null) {
                Surface(
                    color = StatusRedBg,
                    shape = RoundedCornerShape(8.dp),
                    border = BorderStroke(1.dp, StatusRed.copy(alpha = 0.2f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = errorMessage ?: "",
                        fontSize = 12.sp,
                        color = StatusRed,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }

            if (successSaved) {
                Surface(
                    color = StatusGreenBg,
                    shape = RoundedCornerShape(8.dp),
                    border = BorderStroke(1.dp, StatusGreen.copy(alpha = 0.2f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(12.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Outlined.Check,
                            contentDescription = null,
                            tint = StatusGreen,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Configuration saved securely in Android Keystore",
                            fontSize = 12.sp,
                            color = StatusGreen
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Save Button
            Button(
                onClick = {
                    val err = onSaveConfig(host, port, timeout, mtu, autoConnect, deviceName, deviceToken, pinnedFingerprint)
                    if (err != null) {
                        errorMessage = err
                        successSaved = false
                    } else {
                        errorMessage = null
                        successSaved = true
                    }
                },
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = SubtleBlue),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                Text(
                    text = "Save Configuration",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White
                )
            }
        }
    }
}
