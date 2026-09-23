# v1.3.1 acceptance checks

Use disposable or backed-up profiles. Never upload private logs or API keys.

1. Confirm Windows Setup and portable packages, the Linux archive, developer
   ZIP, wheel and sdist all report v1.3.1; verify each platform SHA-256 manifest.
2. Upgrade an installed Windows v1.3.0 copy through **Updates**. Check the
   verified Setup handoff and preservation of settings, characters, campaigns
   and memory. Separately test the portable fresh-folder workflow.
3. Upgrade Linux v1.3.0 through **Updates** into a fresh folder. Run
   `bash install-linux.sh` there, start the client and check saved data. Keep
   the old folder for rollback.
4. In both clients, edit the user-language draft and Generate/Shorter/Longer,
   translate to game language, edit and refine that draft, then translate back
   for review. Test each Clear control, F8/F9 and explicit paste.
5. Paste a draft containing curly apostrophes, quotation marks and dashes into
   NWN. Confirm game chat uses readable punctuation while the editor retains
   the original text. Check accented words in a multilingual session.
6. Check live chat capture, Guardrails & Usage, and update reporting on Windows
   and native Ubuntu. On Wayland use manual paste; on X11 check game input.

Run the root and Linux-layout suites, Ruff, source-integrity guard, package
build, native Linux smoke and update rehearsal before publication. The v1.3.0
client should show v1.3.1 only after GitHub publishes the stable release with
the platform asset and checksum file.
