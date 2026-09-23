# Release job — PowerShell task (Run on agent)
# Display name: Print download paths

$fileName = "$(NewArtifactName)"

Write-Host ""
Write-Host "Download from Artifacts share (SMB):"
Write-Host "  \\100.16.xx.101\Artifacts\Releases\data\$fileName"
Write-Host "  \\network-share-1\Artifacts\Releases\data\$fileName"
Write-Host ""
Write-Host "Download via IIS (Windows Auth or Anonymous per folder config):"
Write-Host "  http://100.16.xx.101:8000/Releases/data/$fileName"
Write-Host "  http://network-share-1:8000/Releases/data/$fileName"
Write-Host ""
Write-Host "Folder browse:"
Write-Host "  http://100.16.xx.101:8000/Releases/data/"
Write-Host ""
