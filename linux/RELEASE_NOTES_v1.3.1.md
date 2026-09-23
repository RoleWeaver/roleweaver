# Role Weaver v1.3.1 — Linux

This maintenance release adds independent Clear controls for both editable
drafts, lets you refine the selected draft in its own language, and normalizes
typographic punctuation when text is copied or pasted into NWN. The editable
text stays unchanged. Shared draft transitions and developer documentation
reduce Windows/Linux drift.

From v1.3.0, open **Updates**, then **Check for Updates** and **Download
Update**. After checksum verification, **Prepare New Folder** copies supported
saved data without overwriting your old installation. Close the old client and
run `bash install-linux.sh` followed by `bash start-role-weaver.sh` in the new
folder. Back up first; do not unpack an archive over the old folder. See
[installation](INSTALL_LINUX.md) and [testing](TESTING_v1.3.1.md).

X11 retains global hotkeys and automatic game input. Wayland requires on-screen
controls and manual paste. Player edits after generation are not subject to
the generated-output guardrail check.
