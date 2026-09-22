# v1.3.0 Linux acceptance checks

1. Extract the Linux release archive to a fresh folder and run
   `bash install-linux.sh`, then `bash start-role-weaver.sh` as a normal user.
2. Verify source/package version 1.3.0, desktop launch, live log capture and
   rapid chat messages with correct speaker and accents.
3. Test Translate Last 3, Continuous Translation, Language Settings and both
   editable F8/F9 draft stages. Confirm protected terms survive translation.
4. Confirm Guardrails AI status, PG policy defaults, Restore Defaults, request
   counts, provider-reported tokens and configured cost estimates.
5. Confirm Updates reports the latest stable version. The simulated GUI
   rehearsal runs under Xvfb in CI; a real newer version is required to test
   GitHub download and fresh-folder preparation from a published release.
6. Test X11 keyboard/paste behavior with NWN/NWN2. On Wayland, verify manual
   copy/paste and no automatic AFK sending or global hotkeys.
7. Back up personal data and verify it survives a fresh-folder upgrade. Run
   `bash install-linux.sh` again in the prepared new folder before launch.

From the Linux client folder, run `.venv/bin/python -m unittest discover -s
tests -v`. Do not include real API keys, personal logs or private Tells in a
test report.
