# v1.3.1 Linux acceptance checks

1. From v1.3.0, use **Updates** to check for v1.3.1, download and verify the
   Linux archive, and prepare a new folder. Run `bash install-linux.sh` there
   before starting. Confirm saved data migrated and the old copy remains.
2. Check live chat capture and accented text. Exercise F8/F9, both editable
   drafts, refinement in each language, translation in both directions, Clear,
   and explicit paste. Curly punctuation should be readable in NWN chat.
3. Confirm Guardrails & Usage still reports requests and provider token counts.
4. Test X11 game input; on Wayland confirm on-screen controls and manual paste.
5. Verify the Linux archive's SHA-256 entry and source/package version 1.3.1.

Run `.venv/bin/python -m unittest discover -s tests -v` from the Linux client
folder. Use only synthetic or backed-up profiles in test reports.
