# Linux testing — 1.2.3

Follow [TESTING_v1.2.3.md](TESTING_v1.2.3.md) and [INSTALL_LINUX.md](INSTALL_LINUX.md).
Run .venv/bin/python -m unittest discover -s tests from the client directory.
On X11, test F8/F9 and F10 AFK. On Wayland, test manual copy/paste and confirm
automatic AFK sending is unavailable.
