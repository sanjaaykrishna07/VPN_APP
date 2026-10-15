package com.quantumsafe.vpn.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ListAlt
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Security
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quantumsafe.vpn.model.VpnUiState
import com.quantumsafe.vpn.ui.screens.*
import com.quantumsafe.vpn.ui.theme.*

enum class AppScreen(val label: String, val icon: ImageVector) {
    HOME("Home", Icons.Outlined.Home),
    CONFIG("Server", Icons.Outlined.Tune),
    SECURITY("Security", Icons.Outlined.Security),
    SETTINGS("Logs", Icons.AutoMirrored.Outlined.ListAlt)
}

@Composable
fun MainScreen(
    state: VpnUiState,
    onToggleVpn: () -> Unit,
    onSetQuantumSafeMode: (Boolean) -> Unit,
    onSetInspectionEnabled: (Boolean) -> Unit,
    onRunShorDemonstration: () -> Unit,
    onSaveConfig: (String, String, String, String, Boolean, String, String, String) -> String?,
    onClearLogs: () -> Unit,
    modifier: Modifier = Modifier
) {
    var currentScreen by remember { mutableStateOf(AppScreen.HOME) }

    Scaffold(
        bottomBar = {
            NavigationBar(
                containerColor = WhiteBackground,
                tonalElevation = 0.dp
            ) {
                AppScreen.values().forEach { screen ->
                    val isSelected = currentScreen == screen
                    NavigationBarItem(
                        selected = isSelected,
                        onClick = { currentScreen = screen },
                        icon = {
                            Icon(
                                imageVector = screen.icon,
                                contentDescription = screen.label
                            )
                        },
                        label = {
                            Text(
                                text = screen.label,
                                fontSize = 11.sp
                            )
                        },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = SubtleBlue,
                            selectedTextColor = SubtleBlue,
                            unselectedIconColor = CharcoalMuted,
                            unselectedTextColor = CharcoalMuted,
                            indicatorColor = SubtleBlueContainer
                        )
                    )
                }
            }
        },
        containerColor = WhiteBackground,
        modifier = modifier
    ) { paddingValues ->
        when (currentScreen) {
            AppScreen.HOME -> HomeScreen(
                state = state,
                onToggleVpn = onToggleVpn,
                onSetQuantumSafeMode = onSetQuantumSafeMode,
                onSetInspectionEnabled = onSetInspectionEnabled,
                onRunShorDemonstration = onRunShorDemonstration,
                onNavigateToConfig = { currentScreen = AppScreen.CONFIG },
                onNavigateToSettings = { currentScreen = AppScreen.SETTINGS },
                modifier = Modifier.padding(paddingValues)
            )
            AppScreen.CONFIG -> ServerConfigScreen(
                currentConfig = state.serverConfig,
                onSaveConfig = onSaveConfig,
                onNavigateBack = { currentScreen = AppScreen.HOME },
                modifier = Modifier.padding(paddingValues)
            )
            AppScreen.SECURITY -> SecurityDetailsScreen(
                onNavigateBack = { currentScreen = AppScreen.HOME },
                modifier = Modifier.padding(paddingValues)
            )
            AppScreen.SETTINGS -> SettingsScreen(
                state = state,
                onClearLogs = onClearLogs,
                onNavigateBack = { currentScreen = AppScreen.HOME },
                modifier = Modifier.padding(paddingValues)
            )
        }
    }
}
