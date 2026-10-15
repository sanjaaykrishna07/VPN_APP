$ErrorActionPreference = "Stop"

$distDir = "D:\VPN_APP\dist"
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Force -Path $distDir
}

$debugApk = "D:\VPN_APP\android\app\build\outputs\apk\debug\app-debug.apk"
$releaseApk = "D:\VPN_APP\android\app\build\outputs\apk\release\app-release.apk"

$destDebug = "D:\VPN_APP\dist\QuantumSafe-VPN-debug.apk"
$destRelease = "D:\VPN_APP\dist\QuantumSafe-VPN-release.apk"

Copy-Item -Path $debugApk -Destination $destDebug -Force
Copy-Item -Path $releaseApk -Destination $destRelease -Force

Write-Host "Files in dist:"
Get-ChildItem $distDir

$hashes = Get-FileHash -Path "$distDir\*.apk" -Algorithm SHA256
$hashes | Format-Table -AutoSize
$hashes | Out-File -FilePath "$distDir\SHA256SUMS.txt" -Encoding utf8

$apksigner = "C:\Users\sanjaay krishna\AppData\Local\Android\Sdk\build-tools\35.0.0\apksigner.bat"
if (Test-Path $apksigner) {
    Write-Host "`n--- Verifying Debug APK Signature ---"
    & $apksigner verify --verbose $destDebug
    Write-Host "`n--- Verifying Release APK Signature ---"
    & $apksigner verify --verbose $destRelease
}
