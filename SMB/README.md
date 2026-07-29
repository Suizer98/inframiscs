# SMB Network Share Server — SMB and IIS

Windows file server for release packages: SMB for CI/CD copy, IIS for browser download with Windows Authentication.

Scripts (run elevated on the target server):

- `setup_window_samba.ps1` — folders, SMB share, NTFS ACLs
- `setup_IIS.ps1` — IIS site, Windows Auth, firewall, HTTP smoke test

---

## 1. Sample environment

Replace with your real host when deploying.


| Item                        | Sample value                            |
| --------------------------- | --------------------------------------- |
| Server IP                   | `100.16.xx.101`                         |
| Hostname                    | `network-share-1`                       |
| Local admin (pipeline copy) | `network-share-1\Administrator`         |
| Share name                  | `Artifacts`                             |
| Physical path               | `C:\Artifacts`                          |
| Packages folder             | `C:\Artifacts\Packages`                 |
| SMB UNC (packages)          | `\\100.16.xx.101\Artifacts\Packages`    |
| HTTP URL (packages)         | `http://100.16.xx.101:8000/Packages/`   |
| IIS site / port             | `Artifacts` / `8000`                    |
| Auth                        | Windows Authentication (Anonymous off)  |


```text
Test-NetConnection 100.16.xx.101 -Port 445
Test-NetConnection 100.16.xx.101 -Port 8000

\\100.16.xx.101\Artifacts\Packages
\\network-share-1\Artifacts\Packages
http://100.16.xx.101:8000/Packages/
```

Use the IP URL for HTTP. Browsers may treat IPs as Internet zone and return `401` until you enter credentials (see Browser access).

---

## 2. Prerequisites

- RDP as local or domain admin to `network-share-1` (`100.16.xx.101`)
- TCP `445` (SMB) and `8000` (HTTP) reachable
- Accounts/groups that should download packages
- Pipeline secrets for the copy account

Grant RDP if needed (then sign out/reconnect):

```powershell
Add-LocalGroupMember -Group "Remote Desktop Users" -Member "CONTOSO\jdoe"
Add-LocalGroupMember -Group "Administrators" -Member "CONTOSO\jdoe"
```

---

## 3. Folders and SMB share

```powershell
.\setup_window_samba.ps1 `
  -WriterAccounts @("CONTOSO\jdoe","network-share-1\Administrator") `
  -ReaderAccounts @("CONTOSO\Domain Users")
```

Manual equivalent:

```powershell
New-Item -Path "C:\Artifacts\Packages" -ItemType Directory -Force

New-SmbShare -Name "Artifacts" -Path "C:\Artifacts" `
  -FullAccess "CONTOSO\jdoe","network-share-1\Administrator"

icacls "C:\Artifacts" /grant "CONTOSO\jdoe:(OI)(CI)(M)" /T
icacls "C:\Artifacts" /grant "network-share-1\Administrator:(OI)(CI)(F)" /T

# Readers (prefer a dedicated group long-term, e.g. CONTOSO\Artifacts-Readers)
icacls "C:\Artifacts" /grant "CONTOSO\Domain Users:(OI)(CI)(RX)" /T
icacls "C:\Artifacts" /grant "FABRIKAM\Domain Users:(OI)(CI)(RX)" /T

Get-SmbShare -Name Artifacts
Get-SmbShareAccess -Name Artifacts
icacls "C:\Artifacts"
```

---



## 4. Test SMB from a client

Test from another machine or the build agent, not only loopback on the server.

```powershell
$password = Read-Host "Password for network-share-1\Administrator" -AsSecureString
$creds = New-Object System.Management.Automation.PSCredential ("network-share-1\Administrator", $password)

net use \\100.16.xx.101\Artifacts /delete /y 2>$null

New-PSDrive -Name Z -PSProvider FileSystem -Root "\\100.16.xx.101\Artifacts" -Credential $creds
Get-ChildItem Z:\Packages
"hello" | Set-Content Z:\Packages\test.txt
Remove-PSDrive Z
net use \\100.16.xx.101\Artifacts /delete /y

Test-NetConnection 100.16.xx.101 -Port 445
```

---

## 5. IIS (browser exposure)

```powershell
.\setup_IIS.ps1
```

Manual steps (port 80 is usually Default Web Site; use 8000):

```powershell
Install-WindowsFeature Web-Server, Web-Windows-Auth, Web-Dir-Browsing -IncludeManagementTools
Import-Module WebAdministration

New-WebAppPool -Name "ArtifactsPool"
# Remove-Website -Name "Artifacts"   # if recreating
New-Website -Name "Artifacts" -Port 8000 -IPAddress "*" `
  -PhysicalPath "C:\Artifacts" -ApplicationPool "ArtifactsPool"

Start-Service WAS
Start-Service W3SVC
iisreset /restart
Start-WebAppPool -Name "ArtifactsPool"
Start-Website -Name "Artifacts"
```

Auth sections are locked at machine level — set via `MACHINE/WEBROOT/APPHOST` with `-Location`:

```powershell
Set-WebConfigurationProperty `
  -Filter "/system.webServer/security/authentication/anonymousAuthentication" `
  -PSPath "MACHINE/WEBROOT/APPHOST" -Location "Artifacts" `
  -Name enabled -Value $false

Set-WebConfigurationProperty `
  -Filter "/system.webServer/security/authentication/windowsAuthentication" `
  -PSPath "MACHINE/WEBROOT/APPHOST" -Location "Artifacts" `
  -Name enabled -Value $true

Set-WebConfigurationProperty `
  -Filter "/system.webServer/directoryBrowse" `
  -PSPath "IIS:\Sites\Artifacts" `
  -Name enabled -Value $true

# Needed so downloads with + in the filename work (otherwise IIS 404.11)
Set-WebConfigurationProperty `
  -Filter "/system.webServer/security/requestFiltering" `
  -PSPath "MACHINE/WEBROOT/APPHOST" -Location "Artifacts" `
  -Name allowDoubleEscaping -Value $true
```

Firewall and smoke test:

```powershell
New-NetFirewallRule -DisplayName "Artifacts HTTP 8000" `
  -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

Invoke-WebRequest "http://localhost:8000/" -UseDefaultCredentials -UseBasicParsing
Invoke-WebRequest "http://localhost:8000/Packages/" -UseDefaultCredentials -UseBasicParsing
# Expect StatusCode 200
```

Confirm sites: Default Web Site on `*:80:`, Artifacts on `*:8000:`.

```powershell
Get-Website | Select-Object Name, State, @{
  n = 'Bindings'
  e = { ($_.bindings.Collection | ForEach-Object bindingInformation) -join ', ' }
}

Get-Service W3SVC, WAS
Get-WebAppPoolState -Name "ArtifactsPool"
```

---

## 6. Browser access

Use the IP URL: `http://100.16.xx.101:8000/Packages/`.

Browsers may return `401` on first visit (IP treated as Internet zone) — not a broken site. Enter `DOMAIN\user` when prompted (InPrivate/Incognito if needed).

Users still need NTFS read on `C:\Artifacts`.

---

## 7. Troubleshooting — download 404 when filename contains `+`

If the file exists on disk and SMB can open it, but HTTP returns a generic 404, IIS request filtering is often rejecting `+` as a double-escape sequence (`404.11`). Remote browsers only show a plain 404; the substatus is visible from the server:

```powershell
Invoke-WebRequest "http://localhost:8000/Packages/.../SomeName+AnotherOne-....zip" `
  -UseDefaultCredentials -UseBasicParsing
```

Or check the IIS log for `404 11`:

```powershell
$logDir = "C:\inetpub\logs\LogFiles\W3SVC$((Get-Website -Name Artifacts).id)"
Get-ChildItem $logDir | Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
  Get-Content | Select-String " 404 "
```

Site fix (also applied by `setup_IIS.ps1`):

```powershell
Set-WebConfigurationProperty `
  -Filter "/system.webServer/security/requestFiltering" `
  -PSPath "MACHINE/WEBROOT/APPHOST" -Location "Artifacts" `
  -Name allowDoubleEscaping -Value $true

Restart-WebAppPool -Name "ArtifactsPool"
```

Longer term, avoid `+` in artifact names so links stay copy-pasteable without that setting. In the release naming script:

```powershell
$envName = "$(Release.EnvironmentName)" -replace '[^\w\.-]', '-'
$newArtifactName = "$(Release.DefinitionName)-$envName-$(Build.BuildNumber)-$(Release.ReleaseName).zip"
```

Rename existing files in place if needed:

```powershell
Get-ChildItem "C:\Artifacts\Packages" -Filter "*+*" -Recurse |
  Rename-Item -NewName { $_.Name -replace '\+', '-' }
```

---

## 8. Sample CI/CD — copy to SMB with powershell task on ADO server

Map the share, copy the package, then clean up the drive (avoids multiple-credential SMB errors):

```powershell
$password = ConvertTo-SecureString "$(SharePassword)" -AsPlainText -Force
$creds = New-Object System.Management.Automation.PSCredential ("$(ShareAccount)", $password)

$share = "\\100.16.xx.101\Artifacts"
$src   = "$(ArtifactPath)"
$dst   = "Z:\Packages\$(ArtifactName)"

Get-PSDrive -Name Z -ErrorAction SilentlyContinue | Remove-PSDrive -Force -ErrorAction SilentlyContinue
cmd /c "net use $share /delete /y" 2>&1 | Out-Null

try {
    New-PSDrive -Name "Z" -PSProvider FileSystem -Root $share -Credential $creds | Out-Null
    New-Item -Path (Split-Path $dst -Parent) -ItemType Directory -Force | Out-Null
    Copy-Item -Path $src -Destination $dst -Force
}
finally {
    Remove-PSDrive -Name "Z" -Force -ErrorAction SilentlyContinue
    cmd /c "net use $share /delete /y" 2>&1 | Out-Null
    $global:LASTEXITCODE = 0
}

Write-Host "SMB : \\100.16.xx.101\Artifacts\Packages\"
Write-Host "HTTP: http://100.16.xx.101:8000/Packages/"
```
Use pipeline variables for `ShareAccount`, `SharePassword`, `ArtifactPath`, and `ArtifactName`.

