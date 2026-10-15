package com.quantumsafe.vpn.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val WhiteBackground = Color(0xFFFFFFFF)
val SurfaceCard = Color(0xFFF8F9FA)
val SurfaceVariant = Color(0xFFF1F3F5)
val CharcoalPrimary = Color(0xFF1A1D20)
val CharcoalSecondary = Color(0xFF495057)
val CharcoalMuted = Color(0xFF868E96)
val SubtleBlue = Color(0xFF1971C2)
val SubtleBlueHover = Color(0xFF1864AB)
val SubtleBlueContainer = Color(0xFFE7F5FF)
val BorderLight = Color(0xFFDEE2E6)
val DividerLight = Color(0xFFE9ECEF)
val StatusGreen = Color(0xFF2B8A3E)
val StatusGreenBg = Color(0xFFEBFBEE)
val StatusAmber = Color(0xFFE67700)
val StatusAmberBg = Color(0xFFFFF9DB)
val StatusRed = Color(0xFFC92A2A)
val StatusRedBg = Color(0xFFFFE3E3)

private val MinimalWhiteColorScheme = lightColorScheme(
    primary = SubtleBlue,
    onPrimary = Color.White,
    primaryContainer = SubtleBlueContainer,
    onPrimaryContainer = SubtleBlueHover,
    background = WhiteBackground,
    onBackground = CharcoalPrimary,
    surface = SurfaceCard,
    onSurface = CharcoalPrimary,
    surfaceVariant = SurfaceVariant,
    onSurfaceVariant = CharcoalSecondary,
    outline = BorderLight,
    outlineVariant = DividerLight
)

@Composable
fun QuantumSafeTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = MinimalWhiteColorScheme,
        content = content
    )
}
