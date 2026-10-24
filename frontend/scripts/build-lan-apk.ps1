<#
.SYNOPSIS
  Builds a release APK that talks to the Django backend running on this PC over the LAN.

.DESCRIPTION
  1. Works out this PC's LAN IP (the adapter with a default gateway, so VPN/VMware adapters are skipped).
  2. Checks the backend answers at http://<ip>:<port>/healthz and that backend/.env allows the IP.
  3. Bakes EXPO_PUBLIC_API_URL into the build (which also allows plain http:// on Android).
  4. Runs `expo prebuild` + `gradlew assembleRelease` and copies the APK to dist/.

  Start the backend first, from backend/:
      venv\Scripts\python manage.py runserver 0.0.0.0:8000

.EXAMPLE
  .\scripts\build-lan-apk.ps1
.EXAMPLE
  .\scripts\build-lan-apk.ps1 -Ip 192.168.0.106 -Install
.EXAMPLE
  .\scripts\build-lan-apk.ps1 -SkipPrebuild      # faster rebuild when only JS changed
.EXAMPLE
  .\scripts\build-lan-apk.ps1 -AllAbis           # also 32-bit ARM and x86 (emulators); slower
#>
[CmdletBinding()]
param(
    [string]$Ip,                      # LAN IP of this PC (auto-detected if omitted)
    [int]$Port = 8000,                # backend port
    [switch]$SkipPrebuild,            # reuse the existing android/ folder
    [switch]$SkipHealthCheck,         # build even if the backend isn't running yet
    [switch]$Install,                 # install on a USB-connected phone with adb
    [switch]$AllAbis                  # build every CPU type, not just arm64-v8a (much slower)
)

$ErrorActionPreference = 'Stop'
$frontend = Split-Path -Parent $PSScriptRoot

# One build at a time: each run stops Gradle's daemons, which would kill a build already running.
# Windows releases the mutex when this process exits, even if it crashes.
$lock = New-Object System.Threading.Mutex($false, 'Local\guru-drishti-build-lan-apk')
try { $haveLock = $lock.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $haveLock = $true }
if (-not $haveLock) {
    Write-Host '    x Another APK build is already running; wait for it to finish.' -ForegroundColor Red
    exit 1
}
$backendEnv = Join-Path (Split-Path -Parent $frontend) 'backend\.env'

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

# --- 1. LAN IP -------------------------------------------------------------------------
Step 'Finding the LAN IP'
if (-not $Ip) {
    $config = Get-NetIPConfiguration |
        Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up' } |
        Select-Object -First 1
    if ($null -eq $config) { Fail 'No connected network adapter with a gateway. Pass -Ip 192.168.x.x' }
    $Ip = ($config.IPv4Address | Select-Object -First 1).IPAddress
    Write-Host "    $Ip ($($config.InterfaceAlias))"
} else {
    Write-Host "    $Ip (given)"
}
$apiUrl = "http://${Ip}:$Port"

# --- 2. Backend checks -----------------------------------------------------------------
Step "Checking the backend at $apiUrl"
if (Test-Path $backendEnv) {
    $hosts = Select-String -Path $backendEnv -Pattern '^\s*ALLOWED_HOSTS\s*=\s*(.*)$' | Select-Object -Last 1
    if ($hosts) {
        $list = $hosts.Matches[0].Groups[1].Value.Split(',') | ForEach-Object { $_.Trim() }
        if (($list -notcontains $Ip) -and ($list -notcontains '*')) {
            Warn "backend/.env ALLOWED_HOSTS doesn't include $Ip; the app will get 400 Bad Request."
            Warn "Add it: ALLOWED_HOSTS=$($list -join ','),$Ip  (then restart runserver)"
        }
    }
}
if (-not $SkipHealthCheck) {
    try {
        $r = Invoke-WebRequest -Uri "$apiUrl/healthz" -UseBasicParsing -TimeoutSec 5
        Write-Host "    backend is up ($($r.StatusCode))"
    } catch {
        Warn "No answer from $apiUrl/healthz."
        Warn 'Start it with: venv\Scripts\python manage.py runserver 0.0.0.0:8000  (from backend/)'
        Warn 'Or rerun with -SkipHealthCheck to build anyway.'
        exit 1
    }
}

# --- 3. Toolchain ----------------------------------------------------------------------
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

# The SDK's CMake ships ninja 1.10, which can't handle paths over 260 characters, and the
# React Native native builds produce such paths ("Filename longer than 260 characters").
# Ninja 1.12+ supports long paths (Windows long paths must be on too), so upgrade it in place
# once and keep the original as ninja.exe.bak.
$longPaths = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -ErrorAction SilentlyContinue).LongPathsEnabled
if ($longPaths -ne 1) {
    Warn 'Windows long paths are off. In an admin PowerShell run, then reboot:'
    Warn "  Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' LongPathsEnabled 1"
}
$ninjaVersion = '1.12.1'
foreach ($ninja in Get-ChildItem (Join-Path $env:ANDROID_HOME 'cmake\*\bin\ninja.exe') -ErrorAction SilentlyContinue) {
    $current = (& $ninja.FullName --version).Trim()
    if ([version]$current -ge [version]'1.12') { continue }
    Write-Host "    upgrading $($ninja.FullName) ($current -> $ninjaVersion, for long paths)"
    $zip = Join-Path $env:TEMP "ninja-win-$ninjaVersion.zip"
    if (-not (Test-Path $zip)) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -OutFile $zip `
            -Uri "https://github.com/ninja-build/ninja/releases/download/v$ninjaVersion/ninja-win.zip"
    }
    $unpacked = Join-Path $env:TEMP "ninja-win-$ninjaVersion"
    Expand-Archive $zip $unpacked -Force
    $backup = "$($ninja.FullName).bak"
    if (-not (Test-Path $backup)) { Copy-Item $ninja.FullName $backup }
    Copy-Item (Join-Path $unpacked 'ninja.exe') $ninja.FullName -Force
}

# --- 4. Build --------------------------------------------------------------------------
$previousUrl = $env:EXPO_PUBLIC_API_URL
$env:EXPO_PUBLIC_API_URL = $apiUrl
# A new, increasing version code for each build (minutes since 2024-01-01), so a phone treats
# the install as an update and refreshes cached app data such as the launcher icon. It is
# written into the native project by prebuild, so -SkipPrebuild keeps the previous one.
$previousCode = $env:ANDROID_VERSION_CODE
$env:ANDROID_VERSION_CODE = [string][int](((Get-Date).ToUniversalTime() - [datetime]'2024-01-01').TotalMinutes)
Push-Location $frontend
try {
    if (-not $SkipPrebuild -or -not (Test-Path 'android')) {
        Step 'Generating the native project (expo prebuild)'
        # A Gradle/Kotlin daemon left from the last build keeps files in android/ open, and
        # `prebuild --clean` then fails with EBUSY. Stop them and clear the folder ourselves.
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
        # arm64-v8a covers practically every phone from the last several years; building all four
        # CPU types roughly quadruples the native compile time.
        if (-not $AllAbis) { $gradleArgs += '-PreactNativeArchitectures=arm64-v8a' }
        .\gradlew.bat @gradleArgs
        $gradleExit = $LASTEXITCODE
    } finally { Pop-Location; Stop-BuildDaemons }
    if ($gradleExit -ne 0) { Fail 'Gradle build failed.' }

    $apk = 'android\app\build\outputs\apk\release\app-release.apk'
    if (-not (Test-Path $apk)) { Fail "APK not found at $apk" }
    New-Item -ItemType Directory -Force 'dist' | Out-Null
    $out = Join-Path $frontend ("dist\guru-drishti-lan-{0}.apk" -f $Ip.Replace('.', '-'))
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

    Write-Host "`n    Phone and PC must be on the same Wi-Fi. If the phone can't connect, allow port $Port"
    Write-Host '    through Windows Firewall (admin PowerShell, once):'
    Write-Host "      New-NetFirewallRule -DisplayName 'Django dev $Port' -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -Profile Private"
} finally {
    Pop-Location
    $env:EXPO_PUBLIC_API_URL = $previousUrl
    $env:ANDROID_VERSION_CODE = $previousCode
}
