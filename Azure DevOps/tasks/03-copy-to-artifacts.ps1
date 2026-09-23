# Release job — PowerShell task (Run on agent)
# Display name: Copy to Artifacts

$shareRoot = "\\100.16.xx.101\Artifacts"
$password = ConvertTo-SecureString "$(SharePassword)" -AsPlainText -Force
$creds = New-Object System.Management.Automation.PSCredential ("$(ShareAccount)", $password)

Get-PSDrive -Name Z -ErrorAction SilentlyContinue | Remove-PSDrive -Force -ErrorAction SilentlyContinue
cmd /c "net use $shareRoot /delete /y" 2>&1 | Out-Null

try {
  New-PSDrive -Name "Z" -PSProvider FileSystem -Root $shareRoot -Credential $creds | Out-Null

  $destinationDirectory = "Z:\Releases\data"
  if (-not (Test-Path $destinationDirectory)) {
    New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
  }

  $sourcePath = "$(ArtifactPath)"
  if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "Source not found: $sourcePath. Re-run the find-artifact task or check the artifact alias."
  }

  $destinationPath = Join-Path $destinationDirectory "$(NewArtifactName)"
  Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force

  Write-Host "Copied $sourcePath to $destinationPath"
}
finally {
  Remove-PSDrive -Name Z -Force -ErrorAction SilentlyContinue
  cmd /c "net use $shareRoot /delete /y" 2>&1 | Out-Null
  $global:LASTEXITCODE = 0
}
