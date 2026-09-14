# Role Weaver 1.2.2 — Ubuntu Wayland fix

This revision removes the startup rejection on Ubuntu Wayland. The Tk interface
runs through Xwayland. Log reading, AI drafts, character memory, lore, and campaign
features remain available. On Wayland, use the on-screen buttons to generate a
reply and **Copy Edited Draft**; open NWN chat and press Ctrl+V yourself, then
review and press Enter. Global hotkeys, automatic focusing/pasting, and automatic
replies are disabled on Wayland. The X11 backend retains its existing behavior.

## Install on Ubuntu

Extract this package into a new writable folder. Keep your old installation and
data as a backup. In an Ubuntu desktop terminal:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-tk xwayland wl-clipboard xdotool xclip
cd /path/to/RoleWeaver-v1.2.2-Linux-UbuntuFix
bash install-linux.sh
bash start-role-weaver.sh
```

Run the last two commands as your normal user. Xwayland must be enabled by your
desktop session; do not invent a DISPLAY value if the launcher reports it missing.

After starting the bot, use Clipboard Test, then manually paste into NWN chat and
press Escape. Generate a reply, edit it, and use Copy Edited Draft. Copied text is
not recorded as spoken dialogue; the actual NWN log remains authoritative.

To retain an existing installation without moving its data, close Role Weaver,
back up that folder, then replace only these files from this package:
linux_platform.py, linux_start.py, nwn_ai_bot.py, nwn_ai_gui.py, install-linux.sh,
start-role-weaver.sh. Install wl-clipboard and xwayland, then run the launcher.
Do not copy the generic Characters/Campaigns folders over your personal profiles.

Python 3.10+ is required. The package is source-based; installation downloads its
dependencies. Settings and personal data remain beside the application. Default
log discovery includes ~/.local/share/Neverwinter Nights/logs; Browse supports
custom paths. NWN_USER_DIRECTORY can specify a custom user directory.

This remains a testing candidate. The user reported running the prior build in
Docker; that does not establish Wayland or NWN input compatibility. This revision
passed 22 mocked/unit tests and compilation here, but no live Ubuntu session was
available to validate GUI rendering, clipboard paste, or gameplay.

## Acceptance checks on Ubuntu

- Launch on Wayland without the old rejection; verify the title says manual paste.
- Start listening and generate a reply using the buttons.
- Clipboard Test and Copy Edited Draft both paste correctly into NWN manually.
- Automatic replies remain disabled, including with old auto-start settings.
- Memory -> Summarize Now completes; saved data survives restarting the client.
- On X11, rerun the original keyboard and focus tests.

No server/NWNX integration is included.

References: [pynput limitations](https://pynput.readthedocs.io/en/latest/limitations.html)
and [Wayland clipboard utilities](https://github.com/bugaevc/wl-clipboard).
