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
    "--add-data=Campaigns/README.md;Campaigns",
    "--add-data=Lore;Lore",
    "--add-data=RoleplayRules;RoleplayRules",
    "--add-data=README.md;.",
    "--add-data=BACKUP_RECOVERY.md;.",
    "--add-data=EDIT_SUMMARY_RECOVERY.md;.",
    "--add-data=FEEDBACK_FIXES.md;.",
    "--add-data=AFK_MODE.md;.",
    "--add-data=GAME_VERSIONS.md;.",
    "--add-data=NWN2_LOGGING.md;.",
    "--add-data=VERSION;.",
    "--add-data=FIRST_RUN.md;.",
    "--add-data=AI_PROVIDER_SETUP.md;.",
    "--add-data=CHARACTER_PROFILE_GUIDE.md;.",
    "--add-data=PLAYER_GUIDE.md;.",
    "--add-data=DM_GUIDE.md;.",
    "--add-data=AUTOMATIC_LOG_DETECTION.md;.",
    "--add-data=RELEASE_NOTES_v1.3.2.md;.",
    "--add-data=TESTING_v1.3.2.md;."
)

# Include every tracked top-level guide, including installation and Vault submission.
# Git's tracked-file list excludes local credentials, recovery files and runtime logs.
$guideFiles = git ls-files -- '*.md' '*.txt'
if ($LASTEXITCODE -ne 0) { throw "Unable to enumerate tracked documentation." }
foreach ($guide in $guideFiles) {
    if ($guide -notmatch '[/\\]' -and $guide -ne 'requirements.txt') {
        $argument = "--add-data=$guide;."
        if ($addData -notcontains $argument) { $addData += $argument }
    }
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --contents-directory "." `
    --name "RoleWeaver" `
    --icon "assets\RoleWeaver.ico" `
    --paths "src" `
    --collect-all "guardrails" `
    --collect-all "guardrails_ai.regex_match" `
    --collect-all "rfc3987_syntax" `
    @addData `
    nwn_ai_gui.py

if (-not (Test-Path "dist\RoleWeaver\RoleWeaver.exe")) {
    throw "PyInstaller build did not create dist\RoleWeaver\RoleWeaver.exe"
}

if (-not (Test-Path "dist\RoleWeaver\rfc3987_syntax\syntax_rfc3987.lark")) {
    throw "PyInstaller omitted the Guardrails AI RFC 3987 grammar."
}

$smokeResult = Join-Path $env:TEMP "roleweaver-guardrails-smoke-$PID.txt"
$smoke = Start-Process -FilePath (Resolve-Path "dist\RoleWeaver\RoleWeaver.exe") `
    -ArgumentList "--guardrails-smoke `"$smokeResult`"" -WindowStyle Hidden -PassThru
try {
    if (-not $smoke.WaitForExit(90000)) {
        $smoke.Kill()
        throw "Packaged Guardrails AI smoke check timed out."
    }
    if (-not (Test-Path -LiteralPath $smokeResult)) {
        throw "Packaged Guardrails AI smoke check produced no result."
    }
    $smokeText = (Get-Content -LiteralPath $smokeResult -Raw).Trim()
    if ($smoke.ExitCode -ne 0 -or $smokeText -ne "active") {
        throw "Packaged Guardrails AI smoke check failed: $smokeText"
    }
} finally {
    Remove-Item -LiteralPath $smokeResult -ErrorAction SilentlyContinue
}

Write-Host "Built dist\RoleWeaver\RoleWeaver.exe"
