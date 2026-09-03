$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "pyinstaller>=6.0,<7"

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

$addData = @(
    "--add-data=assets;assets",
    "--add-data=Characters;Characters",
    "--add-data=Lore;Lore",
    "--add-data=RoleplayRules;RoleplayRules",
    "--add-data=README.md;.",
    "--add-data=FIRST_RUN.md;.",
    "--add-data=AI_PROVIDER_SETUP.md;.",
    "--add-data=CHARACTER_PROFILE_GUIDE.md;.",
    "--add-data=PLAYER_GUIDE.md;.",
    "--add-data=DM_GUIDE.md;.",
    "--add-data=SUPPORTED_SERVERS.md;."
)

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --contents-directory "." `
    --name "RoleWeaver" `
    --icon "assets\RoleWeaver.ico" `
    @addData `
    nwn_ai_gui.py

if (-not (Test-Path "dist\RoleWeaver\RoleWeaver.exe")) {
    throw "PyInstaller build did not create dist\RoleWeaver\RoleWeaver.exe"
}

Write-Host "Built dist\RoleWeaver\RoleWeaver.exe"
