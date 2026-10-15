@echo off
if "%JAVA_HOME%"=="" set JAVA_HOME=C:\Program Files\Java\jdk-21
if "%ANDROID_HOME%"=="" set ANDROID_HOME=C:\Users\sanjaay krishna\AppData\Local\Android\Sdk
set GRADLE_USER_HOME=d:\VPN_APP\.gradle_home
call "C:\Users\sanjaay krishna\.gradle\wrapper\dists\gradle-8.9-bin\90cnw93cvbtalezasaz0blq0a\gradle-8.9\bin\gradle.bat" --gradle-user-home "%GRADLE_USER_HOME%" %*
