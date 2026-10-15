package com.quantumsafe.vpn.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quantumsafe.vpn.model.VpnStatus
import com.quantumsafe.vpn.model.VpnUiState
import com.quantumsafe.vpn.ui.theme.*

@Composable
fun HomeScreen(
    state: VpnUiState,
    onToggleVpn: () -> Unit,
    onSetQuantumSafeMode: (Boolean) -> Unit,
    onSetInspectionEnabled: (Boolean) -> Unit,
    onRunShorDemonstration: () -> Unit,
    onNavigateToConfig: () -> Unit,
    onNavigateToSettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(WhiteBackground)
            .verticalScroll(scrollState)
            .padding(horizontal = 24.dp, vertical = 20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "QuantumSafe VPN",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = CharcoalPrimary
                )
                Text(
                    text = "Post-Quantum Cryptographic Tunnel",
                    fontSize = 12.sp,
                    color = CharcoalMuted
                )
            }
            IconButton(
                onClick = onNavigateToSettings,
                modifier = Modifier.size(40.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.Settings,
                    contentDescription = "Settings",
                    tint = CharcoalSecondary
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Status Badge
        StatusPill(status = state.status)

        Spacer(modifier = Modifier.height(24.dp))

        // Center Action Area (Main Focus)
        val isConnected = state.status == VpnStatus.CONNECTED
        val isConnecting = state.status == VpnStatus.CONNECTING

        Surface(
            onClick = onToggleVpn,
            enabled = !isConnecting,
            shape = CircleShape,
            color = when {
                isConnected -> Color.White
                isConnecting -> SurfaceVariant
                else -> SubtleBlue
            },
            border = BorderStroke(
                width = if (isConnected) 2.dp else 1.dp,
                color = if (isConnected) BorderLight else SubtleBlue
            ),
            shadowElevation = if (isConnected) 1.dp else 3.dp,
            modifier = Modifier.size(150.dp)
        ) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier.fillMaxSize()
            ) {
                if (isConnecting) {
                    CircularProgressIndicator(
                        color = SubtleBlue,
                        strokeWidth = 3.dp,
                        modifier = Modifier.size(48.dp)
                    )
                } else {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            imageVector = if (isConnected) Icons.Outlined.PowerSettingsNew else Icons.Outlined.Lock,
                            contentDescription = if (isConnected) "Disconnect" else "Connect",
                            tint = if (isConnected) StatusRed else Color.White,
                            modifier = Modifier.size(38.dp)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = if (isConnected) "DISCONNECT" else "CONNECT",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            letterSpacing = 1.sp,
                            color = if (isConnected) CharcoalPrimary else Color.White
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(18.dp))

        // Connection Duration or Status Message
        if (isConnected) {
            val hours = state.metrics.durationSeconds / 3600
            val minutes = (state.metrics.durationSeconds % 3600) / 60
            val seconds = state.metrics.durationSeconds % 60
            val timeFormatted = String.format("%02d:%02d:%02d", hours, minutes, seconds)

            Text(
                text = timeFormatted,
                fontSize = 24.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Medium,
                color = CharcoalPrimary
            )
            Text(
                text = "Session Duration",
                fontSize = 11.sp,
                color = CharcoalMuted
            )
        } else {
            Text(
                text = state.statusMessage,
                fontSize = 13.sp,
                color = CharcoalSecondary,
                textAlign = TextAlign.Center
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Control Toggles Card
        Card(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = SurfaceCard),
            border = BorderStroke(1.dp, BorderLight),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // Quantum-Safe Toggle
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Outlined.Security,
                                contentDescription = null,
                                tint = if (state.serverConfig.quantumSafeMode) StatusGreen else CharcoalMuted,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Quantum-Safe Mode",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = CharcoalPrimary
                            )
                        }
                        Text(
                            text = if (state.serverConfig.quantumSafeMode)
                                "ON: ML-KEM-1024 (Post-Quantum lattice)"
                            else
                                "OFF: X25519 (Classical elliptic curve)",
                            fontSize = 11.sp,
                            color = CharcoalMuted
                        )
                    }
                    Switch(
                        checked = state.serverConfig.quantumSafeMode,
                        onCheckedChange = onSetQuantumSafeMode,
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color.White,
                            checkedTrackColor = StatusGreen,
                            uncheckedThumbColor = Color.White,
                            uncheckedTrackColor = SurfaceVariant
                        )
                    )
                }

                HorizontalDivider(color = DividerLight, thickness = 1.dp)

                // Network Inspection Toggle
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Outlined.TravelExplore,
                                contentDescription = null,
                                tint = if (state.serverConfig.inspectionEnabled) SubtleBlue else CharcoalMuted,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Network Inspection",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = CharcoalPrimary
                            )
                        }
                        Text(
                            text = if (state.serverConfig.inspectionEnabled)
                                "ON: Real-time telemetry & Cryptographic lab"
                            else
                                "OFF: Metadata-only operational logs",
                            fontSize = 11.sp,
                            color = CharcoalMuted
                        )
                    }
                    Switch(
                        checked = state.serverConfig.inspectionEnabled,
                        onCheckedChange = onSetInspectionEnabled,
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color.White,
                            checkedTrackColor = SubtleBlue,
                            uncheckedThumbColor = Color.White,
                            uncheckedTrackColor = SurfaceVariant
                        )
                    )
                }
            }
        }

        // Cryptographic Laboratory Section (visible when Network Inspection is ON)
        if (state.serverConfig.inspectionEnabled) {
            Spacer(modifier = Modifier.height(16.dp))

            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = if (state.serverConfig.quantumSafeMode) StatusGreenBg else StatusAmberBg),
                border = BorderStroke(1.dp, if (state.serverConfig.quantumSafeMode) StatusGreen.copy(alpha = 0.3f) else StatusAmber.copy(alpha = 0.3f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Outlined.Science,
                                contentDescription = null,
                                tint = if (state.serverConfig.quantumSafeMode) StatusGreen else StatusAmber,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Shor's Quantum Attack Lab",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = CharcoalPrimary
                            )
                        }

                        Button(
                            onClick = onRunShorDemonstration,
                            enabled = !state.isAnalyzingShor,
                            shape = RoundedCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (state.serverConfig.quantumSafeMode) StatusGreen else StatusAmber
                            ),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = if (state.isAnalyzingShor) "TESTING..." else "TEST ATTACK",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }
                    }

                    Text(
                        text = "Laboratory simulation demonstrating quantum period-finding factorization against key exchange protocols using synthetic test vectors.",
                        fontSize = 11.sp,
                        color = CharcoalSecondary,
                        lineHeight = 15.sp
                    )

                    state.shorDemoResult?.let { res ->
                        HorizontalDivider(color = DividerLight, thickness = 1.dp)

                        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(
                                text = res.statusMessage,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (res.success) StatusRed else StatusGreen
                            )
                            Text(
                                text = "Execution Time: ${res.executionTimeMs} ms | Modulus: ${res.modulusBitLength}-bit",
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                color = CharcoalMuted
                            )
                            Text(
                                text = "Recovered Session Key: ${res.recoveredKeyHex}",
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                color = CharcoalPrimary
                            )
                            Text(
                                text = "Payload Status: ${res.decryptedPlaintext}",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = if (res.success) StatusRed else StatusGreen
                            )
                            Text(
                                text = res.mathematicalProof,
                                fontSize = 10.sp,
                                color = CharcoalMuted,
                                lineHeight = 14.sp
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Bottom Endpoint & Details Card
        Card(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = SurfaceCard),
            border = BorderStroke(1.dp, BorderLight),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Outlined.VpnKey,
                            contentDescription = null,
                            tint = SubtleBlue,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Server Endpoint",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium,
                            color = CharcoalPrimary
                        )
                    }
                    TextButton(
                        onClick = onNavigateToConfig,
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "Configure",
                            fontSize = 12.sp,
                            color = SubtleBlue
                        )
                    }
                }

                Text(
                    text = "${state.serverConfig.host}:${state.serverConfig.port}",
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace,
                    color = CharcoalSecondary,
                    modifier = Modifier.padding(top = 2.dp, bottom = 12.dp)
                )

                HorizontalDivider(color = DividerLight, thickness = 1.dp)

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    DetailColumn(
                        label = "ASSIGNED IP",
                        value = if (state.status == VpnStatus.CONNECTED) state.metrics.assignedIp else "—"
                    )
                    DetailColumn(
                        label = "ENCRYPTION",
                        value = if (state.status == VpnStatus.CONNECTED) "AES-256-GCM" else "—"
                    )
                    DetailColumn(
                        label = "KEY EXCHANGE",
                        value = if (state.status == VpnStatus.CONNECTED) state.metrics.keyExchange else (if (state.serverConfig.quantumSafeMode) "ML-KEM-1024" else "X25519")
                    )
                }
            }
        }
    }
}

@Composable
fun StatusPill(status: VpnStatus) {
    val (bgColor, textColor, text, icon) = when (status) {
        VpnStatus.CONNECTED -> Quadruple(StatusGreenBg, StatusGreen, "CONNECTED", Icons.Outlined.Lock)
        VpnStatus.CONNECTING -> Quadruple(StatusAmberBg, StatusAmber, "CONNECTING...", Icons.Outlined.LockOpen)
        VpnStatus.ERROR -> Quadruple(StatusRedBg, StatusRed, "ERROR", Icons.Outlined.LockOpen)
        VpnStatus.DISCONNECTED -> Quadruple(SurfaceVariant, CharcoalSecondary, "DISCONNECTED", Icons.Outlined.LockOpen)
    }

    Surface(
        shape = RoundedCornerShape(20.dp),
        color = bgColor,
        border = BorderStroke(1.dp, textColor.copy(alpha = 0.25f))
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = textColor,
                modifier = Modifier.size(14.dp)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text(
                text = text,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.5.sp,
                color = textColor
            )
        }
    }
}

@Composable
fun DetailColumn(label: String, value: String) {
    Column {
        Text(
            text = label,
            fontSize = 10.sp,
            fontWeight = FontWeight.Medium,
            color = CharcoalMuted
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = value,
            fontSize = 12.sp,
            fontWeight = FontWeight.SemiBold,
            color = CharcoalPrimary
        )
    }
}

private data class Quadruple<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)
