# Role Weaver v1.3.2 for macOS

This is the stable macOS release following testing of the v1.3.2 preview. Download the ZIP for your Mac's processor: `arm64` for Apple Silicon or `x86_64` for Intel. The release Assets also include `INSTALL_MACOS.md` and SHA-256 checksums.

Role Weaver supports NWN log discovery, character profiles, AI drafts, translation, edit recovery, backups, automatic replies, and AFK emotes. Automatic game input uses macOS System Events with foreground-process checks. Global function-key hotkeys remain disabled; use the on-screen controls.

The packaged app includes the Guardrails AI grammar data and runs a Guardrails validation check before publication. The Intel build uses a consistent OpenSSL library for its `cryptography` dependency. Both architectures are compiled, ad hoc signed, and checked by GitHub Actions.

To enable game input, grant Role Weaver **Accessibility** access and allow its **Automation** request for System Events. Run **Keyboard Test** with NWN open before enabling Auto Send or AFK. The test pastes an unsent line that you can cancel with Escape.

The app is not Apple notarized, so macOS may require **Open Anyway** on first launch. Personal data is stored in `~/Library/Application Support/RoleWeaver` and is kept when the app is replaced. See `INSTALL_MACOS.md` for installation and troubleshooting steps.

The in-app updater checks stable macOS releases. To install this release over a preview, quit Role Weaver, replace `RoleWeaver.app` in Applications, then reopen it.
