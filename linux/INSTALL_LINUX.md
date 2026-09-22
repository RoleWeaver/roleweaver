# Role Weaver 1.2.3 — Linux installation

Supports NWN and NWN2 editions. Native NWN:EE uses its user-data logs; classic
installations and NWN2 through Wine/Proton may require custom log selection.

Download **RoleWeaver-v1.2.3-Linux.tar.gz** from the
[v1.2.3 release](https://github.com/RoleWeaver/roleweaver/releases/tag/v1.2.3).
Extract into a writable folder. In a full repository checkout, use linux/;
the Linux release archive already contains the client root.

## Ubuntu setup

Install desktop dependencies:

    sudo apt update
    sudo apt install python3 python3-venv python3-pip python3-tk xwayland wl-clipboard xdotool xclip

Open a terminal in the client folder and run as your normal desktop user:

    bash install-linux.sh
    bash start-role-weaver.sh

Python 3.10 through 3.13 is required. The installer creates `.venv` and downloads dependencies.
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

From a version with an **Updates** tab, use **Check for Updates**, then
**Download Update** and **Prepare New Folder**. The new folder receives a copy
of your saved data while the old installation remains intact. Close the old
client before running `bash install-linux.sh` and `bash start-role-weaver.sh`
from the new folder. See the repository's `UPDATES.md` for the complete workflow.

Back up with the existing client's Backup control, then close it. Extract the
new archive into a fresh folder and restore your backup if moving installations.
Do not overwrite personal profiles with generic examples. Rerun install-linux.sh
to install current dependencies. Settings and personal data remain with the client.
See [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md) and
[EDIT_SUMMARY_RECOVERY.md](EDIT_SUMMARY_RECOVERY.md).

## Tests

    .venv/bin/python -m unittest discover -s tests

Follow [TESTING_v1.2.3.md](TESTING_v1.2.3.md) for live-game and AFK checks.
