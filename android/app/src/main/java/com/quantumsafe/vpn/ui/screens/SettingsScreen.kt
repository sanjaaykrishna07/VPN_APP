package com.quantumsafe.vpn.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.DeleteOutline
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quantumsafe.vpn.model.VpnUiState
import com.quantumsafe.vpn.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    state: VpnUiState,
    onClearLogs: () -> Unit,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()

    LaunchedEffect(state.logs.size) {
        if (state.logs.isNotEmpty()) {
            listState.animateScrollToItem(state.logs.size - 1)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Diagnostics & Settings",
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
                actions = {
                    IconButton(onClick = onClearLogs) {
                        Icon(
                            imageVector = Icons.Outlined.DeleteOutline,
                            contentDescription = "Clear Logs",
                            tint = CharcoalSecondary
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
                .padding(horizontal = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Live Traffic Diagnostics Card
            Text(
                text = "Tunnel Diagnostics",
                fontSize = 14.sp,
                fontWeight = FontWeight.SemiBold,
                color = CharcoalPrimary
            )

            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = SurfaceCard),
                border = BorderStroke(1.dp, BorderLight),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            Text("DATA TRANSMITTED", fontSize = 10.sp, color = CharcoalMuted)
                            Text(formatBytes(state.metrics.bytesOut), fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = CharcoalPrimary)
                        }
                        Column {
                            Text("DATA RECEIVED", fontSize = 10.sp, color = CharcoalMuted)
                            Text(formatBytes(state.metrics.bytesIn), fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = CharcoalPrimary)
                        }
                        Column {
                            Text("PACKETS", fontSize = 10.sp, color = CharcoalMuted)
                            Text("↑ ${state.metrics.packetsOut} / ↓ ${state.metrics.packetsIn}", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = CharcoalPrimary)
                        }
                    }
                }
            }

            // Connection Logs
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Connection Logs (${state.logs.size})",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = CharcoalPrimary
                )
            }

            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = SurfaceVariant),
                border = BorderStroke(1.dp, BorderLight),
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
                if (state.logs.isEmpty()) {
                    Box(
                        contentAlignment = Alignment.Center,
                        modifier = Modifier.fillMaxSize()
                    ) {
                        Text(
                            text = "No logs yet. Connect to a server to view tunnel activity.",
                            fontSize = 12.sp,
                            color = CharcoalMuted
                        )
                    }
                } else {
                    LazyColumn(
                        state = listState,
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        items(state.logs) { logLine ->
                            Text(
                                text = logLine,
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                color = when {
                                    logLine.contains("[!]") -> StatusRed
                                    logLine.contains("[+]") || logLine.contains("[✓]") -> StatusGreen
                                    else -> CharcoalPrimary
                                },
                                lineHeight = 15.sp
                            )
                        }
                    }
                }
            }

            // About & Version Card
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = SurfaceCard),
                border = BorderStroke(1.dp, BorderLight),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 12.dp)
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text(
                        text = "QuantumSafe VPN",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = CharcoalPrimary
                    )
                    Text(
                        text = "Version 1.0.0 • Architecture: Android VpnService + Native Kotlin MVVM",
                        fontSize = 11.sp,
                        color = CharcoalMuted
                    )
                }
            }
        }
    }
}

private fun formatBytes(bytes: Long): String {
    return when {
        bytes >= 1024 * 1024 -> String.format("%.2f MB", bytes.toDouble() / (1024 * 1024))
        bytes >= 1024 -> String.format("%.1f KB", bytes.toDouble() / 1024)
        else -> "$bytes B"
    }
}
