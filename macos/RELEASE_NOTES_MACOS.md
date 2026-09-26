# Role Weaver v1.3.2 macOS preview

This preview builds the Role Weaver 1.3.2 client as a native macOS app for Apple Silicon and Intel Macs. It includes the Guardrails AI grammar data file missing from preview5 (and the Windows 1.3.1 package). Both Mac builds now check the file and run Guardrails validation inside the finished app before publication. The app supports NWN log discovery, character profiles, AI drafts, translation, edit recovery, and backups. The fix for the native global hotkey listener crash remains included.

**New testers:** download `INSTALL_MACOS.md` from the release Assets and follow its first-launch, permission, and Keyboard Test steps before enabling Auto Send or AFK.

Automatic replies and AFK emotes can be sent to NWN through macOS System Events. The sender checks the foreground process before opening chat, after opening chat, and before submitting. Manual drafts are pasted without pressing Enter. Use the on-screen controls; global function-key hotkeys are disabled in this preview.

Grant `RoleWeaver` access in **System Settings → Privacy & Security → Accessibility**, and allow its **Automation** request for System Events. Run **Keyboard Test** with NWN open before enabling automatic or AFK sending; the test pastes an unsent line that you can cancel with Escape. These desktop permissions and actual NWN chat behavior still require live testing on a Mac.

Download the ZIP matching your Mac processor, unzip it, and move `RoleWeaver.app` to Applications. The app is ad hoc signed and not notarized; macOS may require **Control-click → Open** on first launch. Personal data is stored in `~/Library/Application Support/RoleWeaver` and is kept when the app is replaced.

The in-app updater checks stable releases only and does not offer macOS previews. Download this preview manually from this release page, replace the old app after quitting it, then check **Guardrails & Usage → Overview** for an active Guardrails AI backend.

This build has automated compilation and unit checks on macOS runners. Live Neverwinter Nights gameplay has not yet been verified on a Mac.
