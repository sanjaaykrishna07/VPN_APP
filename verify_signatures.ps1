$ErrorActionPreference = "Stop"

$env:JAVA_HOME = "C:\Program Files\Java\jdk-21"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

$distDir = "D:\VPN_APP\dist"
$destDebug = "D:\VPN_APP\dist\QuantumSafe-VPN-debug.apk"
$destRelease = "D:\VPN_APP\dist\QuantumSafe-VPN-release.apk"

$apksigner = "C:\Users\sanjaay krishna\AppData\Local\Android\Sdk\build-tools\35.0.0\apksigner.bat"
if (Test-Path $apksigner) {
    Write-Host "`n=== VERIFYING DEBUG APK SIGNATURE ==="
    & $apksigner verify --verbose $destDebug
    Write-Host "`n=== VERIFYING RELEASE APK SIGNATURE ==="
    & $apksigner verify --verbose $destRelease
}
