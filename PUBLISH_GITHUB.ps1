$ErrorActionPreference = "Stop"
$Version = (Get-Content "$PSScriptRoot\VERSION" -Raw).Trim()
$Repo = "https://github.com/RoleWeaver/roleweaver.git"
$Work = Join-Path $env:TEMP "roleweaver-publish-$Version"

if (Test-Path $Work) { Remove-Item $Work -Recurse -Force }
git clone $Repo $Work

# Replace the repository working tree with this prepared distribution while preserving .git.
# Removing the old working tree first ensures obsolete sample logs, named-world folders,
# and superseded documentation are deleted from GitHub rather than left behind.
Get-ChildItem $Work -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force
Get-ChildItem $PSScriptRoot -Force | Where-Object { $_.Name -ne '.git' } | ForEach-Object {
    Copy-Item $_.FullName -Destination $Work -Recurse -Force
}

Push-Location $Work
try {
    git add -A
    git status
    git commit -m "Release v$Version - Stable maintenance release"
    git push origin main
    git tag "v$Version"
    git push origin "v$Version"
    Write-Host "Published source and tag v$Version. GitHub Actions should now build the Windows release."
} finally {
    Pop-Location
}
