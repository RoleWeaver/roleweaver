# Role Weaver v1.3.0 — Linux

This Linux client adds editable incoming/outgoing translation, PG-oriented
guardrail policies, AI request/token/cost-estimate charts, and an Updates tab.
The update flow verifies the Linux archive against the release checksum, then
prepares a new folder with a copy of saved settings, characters, campaigns,
lore and memory. The previous installation remains available for rollback.

For the upgrade from v1.2.3, download and extract the archive manually because
v1.2.3 does not have an Updates tab. Run `bash install-linux.sh` and
`bash start-role-weaver.sh` in the new folder. Never extract the archive over
your current client. See [installation](INSTALL_LINUX.md) and
[testing](TESTING_v1.3.0.md).

X11 retains global hotkeys and automatic game input. Wayland requires on-screen
controls and manual paste. Translation uses the configured AI provider; usage
history does not store prompt or reply text. Player edits after generation are
not subject to the generated-output guardrail check.
