# Building the Windows executable

Role Weaver can be distributed as a self-contained Windows application. End users do not need Python installed.

## Automated GitHub build

The repository contains `.github/workflows/windows-release.yml`.

### Test a build

1. Open the repository on GitHub.
2. Select **Actions**.
3. Select **Build Role Weaver Release**.
4. Choose **Run workflow**.
5. When the job completes, download the versioned `RoleWeaver-Windows` artifact.

The artifact contains:

- `RoleWeaver-Setup-vX.Y.Z.exe` — normal Windows installer.
- `RoleWeaver-Portable-vX.Y.Z.zip` — portable version.
- `RoleWeaver-NeverwinterVault-vX.Y.Z.zip` — Vault-oriented portable version.
- `RoleWeaver-Developer-vX.Y.Z.zip` — complete tracked source tree for contributors.
- `roleweaver_client-X.Y.Z-py3-none-any.whl` — reusable Python package.
- `roleweaver_client-X.Y.Z.tar.gz` — Python source distribution.
- `SHA256SUMS.txt` — checksums for every release asset produced by this job.

### Publish a public release

Create and push a version tag such as:

```text
v1.1.0
```

The same workflow builds the Windows and Linux applications, development
packages and checksums, then attaches the downloads to a GitHub Release.

## Build the development package

Install the development dependencies and build from the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m build
```

The wheel and source distribution are written to `dist\`. See `DEVELOPMENT.md`
for their scope and the complete validation commands. `DEVELOPER_PACKAGE.md`
explains why desktop contributors need the full source ZIP or a Git clone. The
release workflow checks that ZIP with `scripts/check_developer_package.py`.

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
