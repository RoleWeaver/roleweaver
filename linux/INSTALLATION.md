# Role Weaver 1.3.0 — Linux installation

Supports NWN and NWN2 editions. Native NWN:EE uses its user-data logs; classic
installations and NWN2 through Wine/Proton may require custom log selection.

Download **RoleWeaver-v1.3.0-Linux.tar.gz** from the
[v1.3.0 release](https://github.com/RoleWeaver/roleweaver/releases/tag/v1.3.0).
Extract into a writable folder. In a full repository checkout, use linux/;
the Linux release archive already contains the client root.

## Ubuntu setup

Install desktop dependencies:

    sudo apt update
    sudo apt install python3 python3-venv python3-pip python3-tk xwayland wl-clipboard xdotool xclip

Open a terminal in the client folder and run as your normal desktop user:

    bash install-linux.sh
    bash start-role-weaver.sh

Python 3.10 through 3.13 is required. The installer creates .venv and downloads dependencies.
Do not run these two scripts as root.

## X11 and Wayland

X11 supports automatic game input and global F-keys. Use Keyboard Test before
enabling AFK. Wayland uses on-screen controls and manual copy/paste through
Xwayland and wl-clipboard. Global hotkeys and automatic AFK sending are unavailable.

## First run

Follow [FIRST_RUN.md](FIRST_RUN.md). Choose Game Version, locate the client log
receiving new chat, select your character and test the AI connection.
See [GAME_VERSIONS.md](GAME_VERSIONS.md) and [NWN2_LOGGING.md](NWN2_LOGGING.md)
for native, Wine/Proton and NWN2 EE 64-bit paths.

## Updating and recovery

Version 1.2.3 has no Updates tab, so its upgrade to 1.3.0 requires a manual
download. In versions with an Updates tab, use **Download Update** and
**Prepare New Folder** to verify the archive and copy saved data to a new
installation. Run `bash install-linux.sh` in that folder before launching.

Back up with the existing client's Backup control, then close it. Extract the
new archive into a fresh folder and restore your backup if moving installations.
Do not overwrite personal profiles with generic examples. Rerun install-linux.sh
to install current dependencies. Settings and personal data remain with the client.
See [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md) and
[EDIT_SUMMARY_RECOVERY.md](EDIT_SUMMARY_RECOVERY.md).

## Tests

    .venv/bin/python -m unittest discover -s tests

Follow [TESTING_v1.3.0.md](TESTING_v1.3.0.md) for live-game, translation and update checks.
