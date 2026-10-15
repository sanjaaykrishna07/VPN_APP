# QuantumSafeVPN — Android Client Setup & Connection Guide

This guide details how to build, install, and connect the native Kotlin Android client to the QuantumSafeVPN Linux server.

---

## 1. Prerequisites
- Physical Android device running Android 8.0 (API 26) or higher.
- Phone connected to the same Wi-Fi network as the Linux VPN Server.
- Android Studio or Gradle 8.0+.

---

## 2. Building the APK

### Via Command Line (Gradle):
```bash
cd android
./gradlew assembleDebug
```
The resulting debug APK will be generated at:
`android/app/build/outputs/apk/debug/app-debug.apk`

### Via Android Studio:
1. Open Android Studio and select **Open Project**.
2. Select the `android/` directory inside `QuantumSafeVPN`.
3. Click **Build -> Build Bundle(s) / APK(s) -> Build APK(s)**.

---

## 3. Installing on Android Phone

Connect your Android phone via USB with USB Debugging enabled:
```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```
*Or copy the `.apk` file to your phone's storage and tap to install.*

---

## 4. Connecting over Wi-Fi

1. Open the **QuantumSafeVPN** app on your phone.
2. In the **VPN Server IP** field, enter your Linux machine's Wi-Fi / LAN IP (e.g. `11.12.5.8`).
3. In the **Server Port** field, enter `7000`.
4. Tap **CONNECT TO VPN**.
5. When the Android system prompt appears asking for VPN permission (*"QuantumSafeVPN wants to set up a VPN connection"*), tap **OK / Accept**.
6. The key icon will appear in your Android status bar, and status will change to **Connected: 10.8.0.x**.

---

## 5. Verification on Phone
- Open Chrome or any browser on your phone.
- Visit `https://www.google.com` or `https://1.1.1.1`.
- Verify your public IP on `https://ifconfig.me` or `https://whatismyipaddress.com` matches your Linux server's public IP!
