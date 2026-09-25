# Role Weaver for macOS

This folder contains the macOS client derived from the Linux v1.3.1 client. The GitHub Actions workflow compiles `RoleWeaver.app` for Apple Silicon and Intel Macs.

For download and first-launch steps, see [INSTALL_MACOS.md](INSTALL_MACOS.md).

The app supports automatic game input and AFK sending through macOS System Events. Before enabling either mode, open **System Settings → Privacy & Security → Accessibility** and allow `RoleWeaver`; allow its **Automation** request to control System Events when prompted. Use **Keyboard Test** while NWN is running: it opens chat and pastes an unsent test line. Press Escape in NWN to discard that line. Confirm that test before using **Auto Send** or **AFK**. Both modes start off and can be toggled in the Controls panel. Use the on-screen controls; global function-key hotkeys are disabled in this preview. If the game uses a different window or process name, change **Window Title Contains** in settings.

Generate or translate a manual draft, then use the draft controls to place it in the NWN chat field for review. The game log remains the source of truth for what was actually sent. To find logs automatically, NWN:EE should write to `~/Documents/Neverwinter Nights/logs`; the app also checks `~/Library/Application Support/Neverwinter Nights/logs`. Select a log manually if your installation uses another path.

Saved profiles, settings, backups, and other personal data live in `~/Library/Application Support/RoleWeaver`. The app does not need to write inside its `.app` bundle.

To build locally on macOS with Python 3.12:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r macos/requirements.txt 'pyinstaller>=6.0,<7'
python -m pip install --no-deps -e .
python -m PyInstaller --noconfirm --clean --windowed --onedir --name RoleWeaver \
  --osx-bundle-identifier com.roleweaver.client \
  --paths src --paths macos --add-data 'macos/assets:assets' \
  --add-data 'macos/Characters:Characters' --add-data 'macos/Campaigns:Campaigns' \
  --add-data 'macos/Lore:Lore' --add-data 'macos/RoleplayRules:RoleplayRules' \
  --add-data 'macos/VERSION:.' macos/macos_start.py
```
