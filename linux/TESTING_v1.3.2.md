# v1.3.2 Linux acceptance checks

Linux behavior is unchanged from v1.3.1; this release fixes the Windows
Guardrails AI package.

1. Verify the Linux archive, source, and package versions report 1.3.2 and
   its SHA-256 manifest matches the published archive.
2. Use **Updates** from v1.3.1 to prepare a new v1.3.2 folder with saved data.
   Run `bash install-linux.sh` in that folder before launching.
3. Confirm normal Guardrails & Usage status, chat capture, draft generation,
   translation, and manual paste. Check X11/Wayland input limits as available.

Run `.venv/bin/python -m unittest discover -s tests -v` from the Linux client
folder. Use only synthetic or backed-up profiles in test reports.
