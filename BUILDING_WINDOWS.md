# Building the Windows executable

Role Weaver can be distributed as a self-contained Windows application. End users do not need Python installed.

## Automated GitHub build

The repository contains `.github/workflows/windows-release.yml`.

### Test a build

1. Open the repository on GitHub.
2. Select **Actions**.
3. Select **Build Windows Release**.
4. Choose **Run workflow**.
5. When the job completes, download the `RoleWeaver-Windows-v1.0.0` artifact.

The artifact contains:

- `RoleWeaver-Setup-v1.0.0.exe` — normal Windows installer.
- `RoleWeaver-Portable-v1.0.0.zip` — portable version.

### Publish a public release

Create and push a version tag such as:

```text
v1.0.0
```

The same workflow builds the Windows application and attaches both downloads to a GitHub Release automatically.

## Local Windows build

From PowerShell in the repository:

```powershell
.\scripts\build_windows.ps1
```

This creates:

```text
dist\RoleWeaver\RoleWeaver.exe
```

To create the installer, install Inno Setup 6 and compile:

```powershell
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "installer\RoleWeaver.iss"
```

The installer is written to `release\`.

## Why an onedir build?

Role Weaver has editable character, lore, server-rule, settings, and memory files. A one-directory PyInstaller build keeps those resources available beside the executable instead of unpacking them into a temporary directory on every launch.

The installer uses the current user's Local AppData Programs folder so Role Weaver can write its settings and user-created roleplay files without requiring administrator privileges.
