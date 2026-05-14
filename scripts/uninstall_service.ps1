<#
.SYNOPSIS
    Go cai dat AutoFill Cap Don Windows Service.

.PARAMETER NssmPath
    Duong dan den nssm.exe. Mac dinh: "nssm".

.PARAMETER ServiceName
    Ten service can go cai. Mac dinh: "AutoFillCapDon".

.PARAMETER Force
    Khong hoi xac nhan.

.EXAMPLE
    .\uninstall_service.ps1
    .\uninstall_service.ps1 -Force
#>
param(
    [string]$NssmPath = "nssm",
    [string]$ServiceName = "AutoFillCapDon",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "[uninstall] Service '$ServiceName' khong ton tai."
    exit 0
}

if (-not $Force) {
    $confirm = Read-Host "Xac nhan go cai service '$ServiceName'? (y/N)"
    if ($confirm -notin @("y", "Y")) {
        Write-Host "[uninstall] Huy bo."
        exit 0
    }
}

Write-Host "[uninstall] Dung service..."
& $NssmPath stop $ServiceName 2>&1 | Out-Null

Write-Host "[uninstall] Go cai service..."
& $NssmPath remove $ServiceName confirm

Write-Host "[uninstall] Hoan tat. Service '$ServiceName' da duoc xoa."
