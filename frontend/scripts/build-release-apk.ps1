<#
.SYNOPSIS
  Builds a release APK that talks to the deployed backend over HTTPS only.

.DESCRIPTION
  1. Works out the API URL, first match wins:
       -Domain parameter  >  API_DOMAIN environment variable  >  apiUrl in brand.config.js
     A bare host (api.example.com) gets https:// added; http:// is refused.
  2. Checks the server's TLS: TLS 1.2 or newer, a certificate that is valid for the host and
     trusted by Windows, and not about to expire.
  3. Checks the backend answers at https://<host>/healthz.
  4. Runs `expo prebuild` + `gradlew assembleRelease` with EXPO_PUBLIC_API_URL baked in
     (APP_ENV=production, cleartext traffic off) and copies the APK to dist/.

.EXAMPLE
  .\scripts\build-release-apk.ps1 -Domain api.example.com
.EXAMPLE
  $env:API_DOMAIN = 'api.example.com'; .\scripts\build-release-apk.ps1 -Install
.EXAMPLE
  .\scripts\build-release-apk.ps1        # uses apiUrl from brand.config.js
#>
[CmdletBinding()]
param(
    [string]$Domain,                  # api.example.com or https://api.example.com
    [int]$MinCertDays = 14,           # fail if the certificate expires sooner than this
    [switch]$SkipPrebuild,            # reuse the existing android/ folder
    [switch]$Install,                 # install on a USB-connected phone with adb
    [switch]$AllAbis                  # also 32-bit ARM and x86 (emulators); slower
)

$ErrorActionPreference = 'Stop'
$frontend = Split-Path -Parent $PSScriptRoot

# One build at a time, shared with build-lan-apk.ps1: each run stops Gradle's daemons, which
# would kill a build already running.
$lock = New-Object System.Threading.Mutex($false, 'Local\guru-drishti-build-lan-apk')
try { $haveLock = $lock.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $haveLock = $true }
if (-not $haveLock) {
    Write-Host '    x Another APK build is already running; wait for it to finish.' -ForegroundColor Red
    exit 1
}

function Step($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Warn($text) { Write-Host "    ! $text" -ForegroundColor Yellow }
function Fail($text) { Write-Host "    x $text" -ForegroundColor Red; exit 1 }

# Gradle and Kotlin keep background daemons alive between builds; they hold files in android/.
function Stop-BuildDaemons {
    $gradlew = Join-Path $frontend 'android\gradlew.bat'
    if (Test-Path $gradlew) { & $gradlew --stop *> $null }
    Get-CimInstance Win32_Process -Filter "Name='java.exe'" |
        Where-Object { $_.CommandLine -match 'GradleDaemon|KotlinCompileDaemon' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

# --- 1. API URL ------------------------------------------------------------------------
Step 'Working out the API URL'
$source = '-Domain'
$value = $Domain
if (-not $value) { $value = $env:API_DOMAIN; $source = 'API_DOMAIN' }
if (-not $value) {
    $source = 'brand.config.js'
    Push-Location $frontend
    try { $value = (node -p "require('./brand.config').apiUrl").Trim() } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Fail 'Could not read apiUrl from brand.config.js (is Node installed?).' }
}
$value = $value.Trim().TrimEnd('/')
if ($value -match '^http://') { Fail "Refusing plain http:// ($value from $source). Release builds use HTTPS only." }
if ($value -notmatch '^https://') { $value = "https://$value" }
try { $uri = [uri]$value } catch { Fail "Not a valid URL: $value (from $source)" }
if ($uri.AbsolutePath -ne '/') { Fail "Give the server root, not a path: $value (the app adds /api/v1 itself)." }
if ($uri.Host -match '(^|\.)example\.(com|org|net)$') {
    Fail "$($uri.Host) is the placeholder. Pass -Domain, set API_DOMAIN, or update apiUrl in brand.config.js."
}
if ($uri.Host -match '^\d{1,3}(\.\d{1,3}){3}$') { Fail 'Use a domain name; certificates are not issued for bare IPs.' }
$apiUrl = "https://$($uri.Authority)"
Write-Host "    $apiUrl (from $source)"

# --- 2. TLS ----------------------------------------------------------------------------
Step "Checking TLS on $($uri.Host):$($uri.Port)"
$protocols = [System.Security.Authentication.SslProtocols]::Tls12
if ([enum]::GetNames([System.Security.Authentication.SslProtocols]) -contains 'Tls13') {
    $protocols = $protocols -bor [System.Security.Authentication.SslProtocols]::Tls13
}
$tcp = New-Object System.Net.Sockets.TcpClient
try {
    try { $tcp.Connect($uri.Host, $uri.Port) } catch { Fail "Can't reach $($uri.Host):$($uri.Port). Check DNS, the firewall (ufw allow 'Nginx Full') and nginx." }
    # No custom validation callback: Windows checks the chain, the host name and revocation.
    $ssl = New-Object System.Net.Security.SslStream($tcp.GetStream(), $false)
    try {
        $ssl.AuthenticateAsClient($uri.Host, $null, $protocols, $true)
    } catch {
        $reason = if ($_.Exception.InnerException) { $_.Exception.InnerException.Message } else { $_.Exception.Message }
        Fail "TLS handshake failed: $reason (expired, self-signed or wrong-host certificate, or TLS older than 1.2)."
    }
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($ssl.RemoteCertificate)
    $daysLeft = [int]($cert.NotAfter - (Get-Date)).TotalDays
    Write-Host "    protocol: $($ssl.SslProtocol)"
    Write-Host "    issued to: $($cert.GetNameInfo('DnsName', $false))  by: $($cert.GetNameInfo('SimpleName', $true))"
    Write-Host "    expires: $($cert.NotAfter.ToString('yyyy-MM-dd')) ($daysLeft days)"
    if ($daysLeft -lt $MinCertDays) { Fail "Certificate expires in $daysLeft days; renew it first (certbot renew)." }
} finally {
    if ($ssl) { $ssl.Dispose() }
    $tcp.Close()
}

# --- 3. Backend ------------------------------------------------------------------------
Step "Checking $apiUrl/healthz"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
    $health = Invoke-RestMethod -Uri "$apiUrl/healthz" -TimeoutSec 10 -MaximumRedirection 0
} catch {
    Fail "No healthy answer from $apiUrl/healthz: $($_.Exception.Message). Check ALLOWED_HOSTS in .env and systemctl status astrology."
}
# Any site can answer 200; only this backend answers {"status": "ok", "checks": {...}}.
if ($health.status -ne 'ok' -or -not $health.checks) {
    Fail "$apiUrl/healthz answered, but not like this backend does. Is the domain pointing at the right server?"
}
Write-Host "    backend is up (database: $($health.checks.database), ephemeris: $($health.checks.ephemeris))"

# --- 4. Toolchain ----------------------------------------------------------------------
Step 'Checking the Android toolchain'
if (-not $env:ANDROID_HOME) {
    $sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
    if (Test-Path $sdk) { $env:ANDROID_HOME = $sdk } else { Fail 'Android SDK not found; install Android Studio or set ANDROID_HOME.' }
}
if (-not $env:JAVA_HOME) {
    $jbr = 'C:\Program Files\Android\Android Studio\jbr'
    if (Test-Path $jbr) { $env:JAVA_HOME = $jbr } else { Fail 'JDK not found; set JAVA_HOME (JDK 17+).' }
}
Write-Host "    ANDROID_HOME=$env:ANDROID_HOME"
Write-Host "    JAVA_HOME=$env:JAVA_HOME"
# build-lan-apk.ps1 upgrades the SDK's ninja for paths over 260 characters; it only needs doing once.
$longPaths = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -ErrorAction SilentlyContinue).LongPathsEnabled
if ($longPaths -ne 1) { Warn 'Windows long paths are off; native builds may fail with "Filename longer than 260 characters".' }
foreach ($ninja in Get-ChildItem (Join-Path $env:ANDROID_HOME 'cmake\*\bin\ninja.exe') -ErrorAction SilentlyContinue) {
    if ([version](& $ninja.FullName --version).Trim() -lt [version]'1.12') {
        Warn "$($ninja.FullName) is older than 1.12; run build-lan-apk.ps1 once to upgrade it if the build fails on long paths."
    }
}

# --- 5. Build --------------------------------------------------------------------------
# -SkipPrebuild reuses android/, which keeps the manifest of the last build; after a LAN build
# that still allows cleartext http.
if ($SkipPrebuild) {
    $manifest = Join-Path $frontend 'android\app\src\main\AndroidManifest.xml'
    if ((Test-Path $manifest) -and (Select-String -Path $manifest -Pattern 'usesCleartextTraffic="true"' -Quiet)) {
        Fail 'android/ is from an http (LAN) build and allows cleartext traffic. Rerun without -SkipPrebuild.'
    }
}
$previous = @{ url = $env:EXPO_PUBLIC_API_URL; appEnv = $env:APP_ENV; code = $env:ANDROID_VERSION_CODE }
$env:EXPO_PUBLIC_API_URL = $apiUrl
$env:APP_ENV = 'production'
# A new, increasing version code for each build (minutes since 2024-01-01), so a phone treats
# the install as an update. Written into the native project by prebuild.
$env:ANDROID_VERSION_CODE = [string][int](((Get-Date).ToUniversalTime() - [datetime]'2024-01-01').TotalMinutes)
Push-Location $frontend
try {
    if (-not $SkipPrebuild -or -not (Test-Path 'android')) {
        Step 'Generating the native project (expo prebuild)'
        Stop-BuildDaemons
        if (Test-Path 'android') {
            foreach ($try in 1..5) {
                try { Remove-Item -Recurse -Force 'android' -ErrorAction Stop; break }
                catch { Start-Sleep -Seconds 3 }  # antivirus can hold fresh build output briefly
            }
            if (Test-Path 'android') { Fail 'Could not delete android/; close Android Studio or anything using it and retry.' }
        }
        npx expo prebuild --platform android --clean --no-install
        if ($LASTEXITCODE -ne 0) { Fail 'expo prebuild failed.' }
    }

    Step "Building the release APK (API: $apiUrl)"
    Push-Location 'android'
    try {
        $gradleArgs = @('assembleRelease')
        if (-not $AllAbis) { $gradleArgs += '-PreactNativeArchitectures=arm64-v8a' }
        .\gradlew.bat @gradleArgs
        $gradleExit = $LASTEXITCODE
    } finally { Pop-Location; Stop-BuildDaemons }
    if ($gradleExit -ne 0) { Fail 'Gradle build failed.' }

    $apk = 'android\app\build\outputs\apk\release\app-release.apk'
    if (-not (Test-Path $apk)) { Fail "APK not found at $apk" }
    New-Item -ItemType Directory -Force 'dist' | Out-Null
    $out = Join-Path $frontend ("dist\guru-drishti-{0}.apk" -f $uri.Host.Replace('.', '-'))
    Copy-Item $apk $out -Force

    Step 'Done'
    Write-Host "    APK: $out" -ForegroundColor Green
    Write-Host "    Talks to: $apiUrl"
    if (-not $SkipPrebuild) { Write-Host "    Version code: $env:ANDROID_VERSION_CODE" }

    if ($Install) {
        Step 'Installing on the connected phone (adb)'
        $adb = Join-Path $env:ANDROID_HOME 'platform-tools\adb.exe'
        & $adb install -r $out
        if ($LASTEXITCODE -ne 0) { Warn 'adb install failed; is USB debugging on and the phone authorised?' }
    }
} finally {
    Pop-Location
    $env:EXPO_PUBLIC_API_URL = $previous.url
    $env:APP_ENV = $previous.appEnv
    $env:ANDROID_VERSION_CODE = $previous.code
}
