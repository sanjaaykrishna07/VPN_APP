package com.quantumsafe.vpn.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.CheckCircleOutline
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quantumsafe.vpn.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SecurityDetailsScreen(
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Security Details",
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
            // Cryptographic Stack Header
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Outlined.Shield,
                    contentDescription = null,
                    tint = SubtleBlue,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Cryptographic Architecture",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = CharcoalPrimary
                )
            }

            // Specs Card
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = SurfaceCard),
                border = BorderStroke(1.dp, BorderLight),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    SecurityRow(
                        title = "Key Encapsulation (KEM)",
                        value = "ML-KEM-1024 (NIST FIPS 203)",
                        detail = "1568-byte public key / 1568-byte ciphertext"
                    )
                    HorizontalDivider(color = DividerLight, thickness = 1.dp)

                    SecurityRow(
                        title = "Digital Signature (DSA)",
                        value = "ML-DSA-65 (NIST FIPS 204)",
                        detail = "1952-byte server PK / 3309-byte transcript signature"
                    )
                    HorizontalDivider(color = DividerLight, thickness = 1.dp)

                    SecurityRow(
                        title = "Key Derivation Function (KDF)",
                        value = "HKDF-SHA256 (RFC 5869)",
                        detail = "Generates 256-bit symmetric session key with static salt"
                    )
                    HorizontalDivider(color = DividerLight, thickness = 1.dp)

                    SecurityRow(
                        title = "Data Tunnel AEAD",
                        value = "AES-256-GCM (NIST SP 800-38D)",
                        detail = "12-byte random nonce, 16-byte authentication tag"
                    )
                    HorizontalDivider(color = DividerLight, thickness = 1.dp)

                    SecurityRow(
                        title = "Anti-Replay Mechanism",
                        value = "64-bit Monotonic Sequence Counter",
                        detail = "Strict sequential verification per packet"
                    )
                }
            }

            // Wire Protocol Card
            Text(
                text = "Wire Protocol & Handshake",
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
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    HandshakeStep(step = "1", title = "Server Identity", desc = "Server transmits pinned ML-DSA-65 public key")
                    HandshakeStep(step = "2", title = "Ephemeral Exchange", desc = "Client sends ephemeral ML-KEM-1024 public key")
                    HandshakeStep(step = "3", title = "KEM Ciphertext & Signature", desc = "Server returns ciphertext, DSA signature over transcript, and IP configuration")
                    HandshakeStep(step = "4", title = "Key Derivation & TUN", desc = "Client verifies signature, decapsulates secret, derives AES key, and brings up VpnService")
                }
            }

            // Honest Disclosure / Technical Transparency Card
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = SurfaceVariant),
                border = BorderStroke(1.dp, BorderLight),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.Top) {
                    Icon(
                        imageVector = Icons.Outlined.Info,
                        contentDescription = null,
                        tint = CharcoalSecondary,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "Implementation Transparency",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = CharcoalPrimary
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "This application implements the complete NIST FIPS 203/204 wire format specification. On systems without native liboqs C binaries, both the Android client and Python server use deterministic SHA3-256 lattice-simulation fallbacks with matching wire sizes. Local credentials and settings are secured by the Android Keystore system.",
                            fontSize = 11.sp,
                            color = CharcoalSecondary,
                            lineHeight = 16.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
fun SecurityRow(title: String, value: String, detail: String) {
    Column {
        Text(
            text = title,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
            color = CharcoalMuted
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = value,
            fontSize = 13.sp,
            fontWeight = FontWeight.SemiBold,
            color = CharcoalPrimary
        )
        Text(
            text = detail,
            fontSize = 11.sp,
            fontFamily = FontFamily.Monospace,
            color = CharcoalSecondary
        )
    }
}

@Composable
fun HandshakeStep(step: String, title: String, desc: String) {
    Row(verticalAlignment = Alignment.Top) {
        Surface(
            shape = RoundedCornerShape(4.dp),
            color = SubtleBlueContainer,
            modifier = Modifier.size(20.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = step,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = SubtleBlueHover
                )
            }
        }
        Spacer(modifier = Modifier.width(10.dp))
        Column {
            Text(
                text = title,
                fontSize = 12.sp,
                fontWeight = FontWeight.SemiBold,
                color = CharcoalPrimary
            )
            Text(
                text = desc,
                fontSize = 11.sp,
                color = CharcoalMuted
            )
        }
    }
}
