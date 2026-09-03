$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Role Weaver.lnk"
$launcher = Join-Path $root "RoleWeaver.bat"
$icon = Join-Path $root "assets\RoleWeaver.ico"

if (-not (Test-Path $launcher)) {
    throw "RoleWeaver.bat was not found at $launcher"
}

$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $root
if (Test-Path $icon) {
    $shortcut.IconLocation = "$icon,0"
}
$shortcut.Description = "Role Weaver - NWN AI Roleplay Assistant"
$shortcut.Save()

Write-Host "Created desktop shortcut: $shortcutPath"
