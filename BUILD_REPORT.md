# QuantumSafeVPN — Android Application Build Report

## 1. Build Metadata
- **Build Status**: **SUCCESSFUL**
- **Application Name**: QuantumSafeVPN
- **Package Name**: `com.quantumsafe.vpn`
- **Version Name**: `1.0.0`
- **Version Code**: `1`
- **Compile SDK**: `34` (Android 14)
- **Target SDK**: `34` (Android 14)
- **Min SDK**: `26` (Android 8.0 Oreo)
- **Gradle Version**: `8.2.2`
- **Kotlin Version**: `1.9.22`

## 2. Output Artifacts
- **Primary Release APK**: `D:\VPN_APP\releases\QuantumSafeVPN-debug.apk`
- **Gradle Debug APK**: `D:\VPN_APP\android\app\build\outputs\apk\debug\app-debug.apk`
- **File Size**: `19011180` bytes (18565.61 KB)
- **SHA-256 Checksum**: `681f8bba55f561669af7063f5339aa5c461689bdc9efe35d0a3a59b76dca8b67`
- **Checksum File**: `D:\VPN_APP\releases\SHA256SUMS.txt`

## 3. Cryptographic & Subsystem Summary
- **VpnService**: `com.quantumsafe.vpn.QuantumSafeVpnService` with `protect(socket)` loop evasion.
- **Key Exchange**: ML-KEM-1024 (NIST FIPS 203) wire-compatible implementation.
- **Identity Authentication**: ML-DSA-65 (NIST FIPS 204) lattice signature verification.
- **Tunnel AEAD**: AES-256-GCM (NIST FIPS 197) with 64-bit sequence counters.
- **KDF**: HKDF-SHA256 (RFC 5869).
