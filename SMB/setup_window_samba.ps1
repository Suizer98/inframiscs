#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Sets up an Artifacts SMB share on a Windows server.

.DESCRIPTION
  Creates:
  - C:\Artifacts\Packages (or custom paths)
  - SMB share "Artifacts" with NTFS ACLs for writers and readers

  Run elevated on the target server (e.g. network-share-1).
  For IIS browser exposure, run setup_IIS.ps1 separately.

.EXAMPLE
  .\setup_window_samba.ps1

.EXAMPLE
  .\setup_window_samba.ps1 `
    -PhysicalPath "C:\Artifacts" `
    -PackagesFolderName "Packages" `
    -ShareName "Artifacts" `
    -WriterAccounts @("CONTOSO\jdoe","network-share-1\Administrator") `
    -ReaderAccounts @("CONTOSO\Domain Users","FABRIKAM\Domain Users")
#>

[CmdletBinding()]
param(
    [string]$PhysicalPath = "C:\Artifacts",
    [string]$PackagesFolderName = "Packages",
    [string]$ShareName = "Artifacts",
    [string[]]$WriterAccounts = @(),
    [string[]]$ReaderAccounts = @()
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -Path $Path -ItemType Directory -Force | Out-Null
        Write-Host "Created: $Path"
    }
    else {
        Write-Host "Exists:  $Path"
    }
}

$packagesPath = Join-Path $PhysicalPath $PackagesFolderName
$computerName = $env:COMPUTERNAME

Write-Step "Artifacts SMB setup"
Write-Host "Computer : $computerName"
Write-Host "Path     : $PhysicalPath"
Write-Host "Packages : $packagesPath"
Write-Host "Share    : \\$computerName\$ShareName\$PackagesFolderName"

Write-Step "Create folders"
Ensure-Directory -Path $PhysicalPath
Ensure-Directory -Path $packagesPath

if ($WriterAccounts.Count -eq 0) {
    $WriterAccounts = @("$computerName\Administrators")
    Write-Host "No -WriterAccounts supplied; using $computerName\Administrators"
}
if ($ReaderAccounts.Count -eq 0) {
    Write-Host "No -ReaderAccounts supplied; skipping domain reader grants (add later with icacls)."
}

Write-Step "Configure SMB share '$ShareName'"

$existingShare = Get-SmbShare -Name $ShareName -ErrorAction SilentlyContinue
if (-not $existingShare) {
    $fullAccess = @($WriterAccounts)
    New-SmbShare -Name $ShareName -Path $PhysicalPath -FullAccess $fullAccess | Out-Null
    Write-Host "Created share: $ShareName -> $PhysicalPath"
}
else {
    Write-Host "Share already exists: $ShareName -> $($existingShare.Path)"
    if ($existingShare.Path -ne $PhysicalPath) {
        throw "Share '$ShareName' points to '$($existingShare.Path)' but -PhysicalPath is '$PhysicalPath'."
    }
}

foreach ($account in $WriterAccounts) {
    try {
        Grant-SmbShareAccess -Name $ShareName -AccountName $account -AccessRight Full -Force -ErrorAction Stop | Out-Null
        Write-Host "Share FullAccess: $account"
    }
    catch {
        Write-Warning "Could not grant share access to $account : $($_.Exception.Message)"
    }

    try {
        icacls $PhysicalPath /grant "${account}:(OI)(CI)(M)" /T | Out-Null
        Write-Host "NTFS Modify: $account"
    }
    catch {
        Write-Warning "Could not grant NTFS modify to $account : $($_.Exception.Message)"
    }
}

foreach ($account in $ReaderAccounts) {
    try {
        Grant-SmbShareAccess -Name $ShareName -AccountName $account -AccessRight Read -Force -ErrorAction Stop | Out-Null
        Write-Host "Share Read: $account"
    }
    catch {
        Write-Warning "Could not grant share read to $account : $($_.Exception.Message)"
    }

    try {
        icacls $PhysicalPath /grant "${account}:(OI)(CI)(RX)" /T | Out-Null
        Write-Host "NTFS Read/Execute: $account"
    }
    catch {
        Write-Warning "Could not grant NTFS read to $account : $($_.Exception.Message)"
    }
}

Get-SmbShare -Name $ShareName | Format-List Name, Path, ShareState
Get-SmbShareAccess -Name $ShareName | Format-Table Name, AccountName, AccessRight, AccessControlType

Write-Step "Done"
Write-Host "SMB packages: \\$computerName\$ShareName\$PackagesFolderName"
Write-Host ""
Write-Host "Example pipeline destination after mapping the share:"
Write-Host "  Z:\$PackagesFolderName\<package-file>"
Write-Host ""
Write-Host "For browser download, run setup_IIS.ps1 on this server."
