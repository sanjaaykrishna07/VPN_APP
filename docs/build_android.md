# QuantumSafeVPN — Android Application Build Guide

This document describes how to compile, assemble, and package the native Kotlin Android client for QuantumSafeVPN.

---

## 1. Environment & Build Requirements
- Android SDK Platform 34 (Android 14)
- Minimum SDK: Android 8.0 (API level 26)
- Java Development Kit: OpenJDK 17 or Oracle JDK 17
- Gradle: 8.2+
- Kotlin: 1.9.22+

---

## 2. Command-Line Build Instructions

Navigate to the `android/` directory:
```bash
cd android
```

### Build Debug APK:
```bash
./gradlew assembleDebug
```
*On Windows PowerShell:*
```powershell
.\gradlew.bat assembleDebug
```

The output APK will be located at:
`android/app/build/outputs/apk/debug/app-debug.apk`

### Build Release APK:
```bash
./gradlew assembleRelease
```

### Run Unit Tests:
```bash
./gradlew test
```

---

## 3. Android Studio Build Instructions

1. Launch Android Studio.
2. Select **File -> Open...** and choose the `QuantumSafeVPN/android` folder.
3. Allow Gradle to sync dependencies (`androidx.core`, `androidx.appcompat`, `bouncycastle`).
4. Connect an Android device with USB debugging enabled (or start an Android Virtual Device).
5. Click the green **Run** button (or `Shift + F10`) to build and launch the application directly.

---

## 4. Dependencies Included in `app/build.gradle`

```groovy
dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("org.bouncycastle:bcprov-jdk18on:1.77")
}
```
