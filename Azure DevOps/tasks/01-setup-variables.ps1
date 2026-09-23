# Release job — PowerShell task (Run on agent)
# Display name: Setup variables

$searchRoot = "$(System.DefaultWorkingDirectory)"
$matches = Get-ChildItem -Path $searchRoot -Recurse -Filter "Sample_Editing_Tools_*.atbx" -ErrorAction Stop |
  Sort-Object Name -Descending

if (-not $matches) {
  throw "No Sample_Editing_Tools_*.atbx under $searchRoot. Check artifact alias / download."
}

$artifactPath = $matches[0].FullName
$artifactName = Split-Path $artifactPath -Leaf
$artifactNameWithoutExtension = [IO.Path]::GetFileNameWithoutExtension($artifactPath)
$artifactParentDirectory = Split-Path -Parent $artifactPath

# $newArtifactName = "$(Release.DefinitionName)-$(Release.EnvironmentName)-$(Build.BuildNumber)-$(Release.ReleaseName).atbx"
$newArtifactName = $artifactName
$newArtifactPath = $artifactPath
$newArtifactDirectory = Join-Path $artifactParentDirectory $artifactNameWithoutExtension

Write-Host "Found: $artifactPath"
Write-Host "Using name: $newArtifactName"

Write-Host "##vso[task.setvariable variable=ArtifactPath]$artifactPath"
Write-Host "##vso[task.setvariable variable=ArtifactName]$artifactName"
Write-Host "##vso[task.setvariable variable=ArtifactNameWithoutExtension]$artifactNameWithoutExtension"
Write-Host "##vso[task.setvariable variable=ArtifactParentDirectory]$artifactParentDirectory"
Write-Host "##vso[task.setvariable variable=NewArtifactDirectory]$newArtifactDirectory"
Write-Host "##vso[task.setvariable variable=NewArtifactName]$newArtifactName"
Write-Host "##vso[task.setvariable variable=NewArtifactPath]$newArtifactPath"
