# Role Weaver for macOS

This folder contains the macOS client derived from the Linux v1.3.1 client. The GitHub Actions workflow compiles `RoleWeaver.app` for Apple Silicon and Intel Macs.

The app uses manual clipboard handoff for NWN input. Generate or translate a draft, click **Copy Edited Draft**, open NWN chat, press **Command+V**, review, and send. Global hotkeys, auto send, and AFK sending are disabled. To find logs automatically, NWN:EE should write to `~/Documents/Neverwinter Nights/logs`; the app also checks `~/Library/Application Support/Neverwinter Nights/logs`. Select a log manually if your installation uses another path.

Saved profiles, settings, backups, and other personal data live in `~/Library/Application Support/RoleWeaver`. The app does not need to write inside its `.app` bundle.

To build locally on macOS with Python 3.12:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r macos/requirements.txt 'pyinstaller>=6.0,<7'
python -m pip install --no-deps -e .
python -m PyInstaller --noconfirm --clean --windowed --onedir --name RoleWeaver \
  --paths src --paths macos --add-data 'macos/assets:assets' \
  --add-data 'macos/Characters:Characters' --add-data 'macos/Campaigns:Campaigns' \
  --add-data 'macos/Lore:Lore' --add-data 'macos/RoleplayRules:RoleplayRules' \
  --add-data 'macos/VERSION:.' macos/macos_start.py
```
