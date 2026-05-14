<#
.SYNOPSIS
    Cai dat AutoFill Cap Don nhu Windows Service qua NSSM.

.DESCRIPTION
    Script nay dung nssm.exe de dang ky pipeline auto_fill chay nhu Windows Service.
    Nen chay voi quyen Administrator.

.PARAMETER NssmPath
    Duong dan den nssm.exe (mac dinh: "nssm" neu da them vao PATH).

.PARAMETER IntervalMinutes
    Khoang thoi gian poll Outlook (phut). Mac dinh: 15.

.PARAMETER ServiceName
    Ten Windows Service. Mac dinh: "AutoFillCapDon".

.EXAMPLE
    .\install_service.ps1
    .\install_service.ps1 -NssmPath "C:\tools\nssm.exe" -IntervalMinutes 30
#>
param(
    [string]$NssmPath = "nssm",
    [int]$IntervalMinutes = 15,
    [string]$ServiceName = "AutoFillCapDon"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---- Locate Python and project root ----
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $PythonExe) {
    Write-Error "Khong tim thay Python trong PATH. Hay kich hoat virtualenv truoc."
    exit 1
}

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$LogDir      = Join-Path $ProjectRoot "logs"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Write-Host "[install] Service  : $ServiceName"
Write-Host "[install] Python   : $PythonExe"
Write-Host "[install] WorkDir  : $ProjectRoot"
Write-Host "[install] Interval : $IntervalMinutes min"

# ---- Check nssm ----
try {
    & $NssmPath version 2>&1 | Out-Null
} catch {
    Write-Error @"
nssm khong tim thay tai '$NssmPath'.
Tai ve tai https://nssm.cc/download va dat vao PATH, hoac chi ro -NssmPath.
"@
    exit 1
}

# ---- Install / update service ----
$svcArgs = "-m auto_fill schedule --interval $IntervalMinutes"

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[install] Service da ton tai -- cap nhat cau hinh..."
    & $NssmPath stop $ServiceName 2>&1 | Out-Null
} else {
    & $NssmPath install $ServiceName $PythonExe $svcArgs
}

& $NssmPath set $ServiceName Application       $PythonExe
& $NssmPath set $ServiceName AppParameters     $svcArgs
& $NssmPath set $ServiceName AppDirectory      $ProjectRoot
& $NssmPath set $ServiceName AppStdout         (Join-Path $LogDir "service_stdout.log")
& $NssmPath set $ServiceName AppStderr         (Join-Path $LogDir "service_stderr.log")
& $NssmPath set $ServiceName AppRotateFiles    1
& $NssmPath set $ServiceName AppRotateBytes    10485760   # 10 MB
& $NssmPath set $ServiceName AppRotateOnline   1
& $NssmPath set $ServiceName Start             SERVICE_AUTO_START
& $NssmPath set $ServiceName DisplayName       "AutoFill Cap Don"
& $NssmPath set $ServiceName Description       "Tu dong nhap phieu cap don bao hiem tu Outlook vao Excel."

# ---- Start ----
& $NssmPath start $ServiceName

Write-Host ""
Write-Host "[install] Hoan tat. Kiem tra trang thai:"
Write-Host "  Get-Service $ServiceName"
Write-Host "  nssm status $ServiceName"
Write-Host ""
Write-Host "De dung service: nssm stop $ServiceName"
Write-Host "De go cai:        .\uninstall_service.ps1"
