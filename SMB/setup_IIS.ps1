#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Sets up IIS browser exposure for an Artifacts folder on a Windows server.

.DESCRIPTION
  Creates:
  - IIS site on port 8000 with Windows Auth + directory browsing
  - Firewall rule for the HTTP port

  Expects the physical path (e.g. C:\Artifacts) to already exist.
  Run setup_window_samba.ps1 first if SMB folders are not yet created.

.EXAMPLE
  .\setup_IIS.ps1

.EXAMPLE
  .\setup_IIS.ps1 `
    -PhysicalPath "C:\Artifacts" `
    -PackagesFolderName "Packages" `
    -SiteName "Artifacts" `
    -HttpPort 8000
#>

[CmdletBinding()]
param(
    [string]$PhysicalPath = "C:\Artifacts",
    [string]$PackagesFolderName = "Packages",
    [string]$SiteName = "Artifacts",
    [string]$AppPoolName = "ArtifactsPool",
    [int]$HttpPort = 8000,
    [switch]$SkipFirewall
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

$computerName = $env:COMPUTERNAME

Write-Step "Artifacts IIS setup"
Write-Host "Computer : $computerName"
Write-Host "Path     : $PhysicalPath"
Write-Host "HTTP     : http://${computerName}:$HttpPort/$PackagesFolderName/"

if (-not (Test-Path -LiteralPath $PhysicalPath)) {
    throw "Physical path '$PhysicalPath' does not exist. Run setup_window_samba.ps1 first or create the folder."
}

Write-Step "Install IIS roles (if missing)"
$features = @("Web-Server", "Web-Windows-Auth", "Web-Dir-Browsing")
foreach ($feature in $features) {
    $state = Get-WindowsFeature -Name $feature
    if ($state.InstallState -ne "Installed") {
        Write-Host "Installing $feature ..."
        Install-WindowsFeature -Name $feature -IncludeManagementTools | Out-Null
    }
    else {
        Write-Host "Already installed: $feature"
    }
}

Import-Module WebAdministration

Write-Step "Configure IIS app pool and site"
if (-not (Test-Path "IIS:\AppPools\$AppPoolName")) {
    New-WebAppPool -Name $AppPoolName | Out-Null
    Write-Host "Created app pool: $AppPoolName"
}
else {
    Write-Host "App pool exists: $AppPoolName"
}

$site = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
if ($site) {
    Write-Host "Removing existing site '$SiteName' to recreate cleanly..."
    Stop-Website -Name $SiteName -ErrorAction SilentlyContinue
    Remove-Website -Name $SiteName
}

New-Website -Name $SiteName `
    -Port $HttpPort `
    -IPAddress "*" `
    -PhysicalPath $PhysicalPath `
    -ApplicationPool $AppPoolName | Out-Null
Write-Host "Created site '$SiteName' on port $HttpPort -> $PhysicalPath"

Write-Step "Start IIS services and site"
Start-Service WAS
Start-Service W3SVC
& iisreset /restart | Out-Null
Start-WebAppPool -Name $AppPoolName
Start-Website -Name $SiteName
Write-Host "Site started: $SiteName"

Write-Step "Configure Windows Authentication + directory browsing"
Set-WebConfigurationProperty `
    -Filter "/system.webServer/security/authentication/anonymousAuthentication" `
    -PSPath "MACHINE/WEBROOT/APPHOST" -Location $SiteName `
    -Name enabled -Value $false

Set-WebConfigurationProperty `
    -Filter "/system.webServer/security/authentication/windowsAuthentication" `
    -PSPath "MACHINE/WEBROOT/APPHOST" -Location $SiteName `
    -Name enabled -Value $true

Set-WebConfigurationProperty `
    -Filter "/system.webServer/directoryBrowse" `
    -PSPath "IIS:\Sites\$SiteName" `
    -Name enabled -Value $true

$anon = Get-WebConfigurationProperty -Filter "/system.webServer/security/authentication/anonymousAuthentication" `
    -PSPath "MACHINE/WEBROOT/APPHOST" -Location $SiteName -Name enabled
$win = Get-WebConfigurationProperty -Filter "/system.webServer/security/authentication/windowsAuthentication" `
    -PSPath "MACHINE/WEBROOT/APPHOST" -Location $SiteName -Name enabled
$browse = Get-WebConfigurationProperty -Filter "/system.webServer/directoryBrowse" `
    -PSPath "IIS:\Sites\$SiteName" -Name enabled

Write-Host "Anonymous Auth      : $($anon.Value)"
Write-Host "Windows Auth        : $($win.Value)"
Write-Host "Directory browsing  : $($browse.Value)"

Get-Website | Select-Object Name, State, @{
    n = "Bindings"
    e = { ($_.bindings.Collection | ForEach-Object bindingInformation) -join ", " }
} | Format-Table -AutoSize

if (-not $SkipFirewall) {
    Write-Step "Firewall rule for TCP $HttpPort"
    $ruleName = "Artifacts HTTP $HttpPort"
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if (-not $existingRule) {
        New-NetFirewallRule -DisplayName $ruleName `
            -Direction Inbound -Protocol TCP -LocalPort $HttpPort -Action Allow | Out-Null
        Write-Host "Created firewall rule: $ruleName"
    }
    else {
        Write-Host "Firewall rule already exists: $ruleName"
        Enable-NetFirewallRule -DisplayName $ruleName
    }
}

Write-Step "Local HTTP smoke test"
try {
    $root = Invoke-WebRequest "http://localhost:$HttpPort/" -UseDefaultCredentials -UseBasicParsing
    Write-Host "GET / -> $($root.StatusCode)"
    $pkg = Invoke-WebRequest "http://localhost:$HttpPort/$PackagesFolderName/" -UseDefaultCredentials -UseBasicParsing
    Write-Host "GET /$PackagesFolderName/ -> $($pkg.StatusCode)"
}
catch {
    Write-Warning "Local HTTP test failed: $($_.Exception.Message)"
    Write-Warning "Confirm site is Started and Windows Auth / NTFS are correct."
}

Write-Step "Done"
Write-Host "HTTP packages: http://${computerName}:$HttpPort/$PackagesFolderName/"
Write-Host "Prefer hostname over IP in browsers to avoid 401 with Windows Auth."
