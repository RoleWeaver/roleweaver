# Role Weaver v1.3.1 macOS preview

This preview builds the Role Weaver 1.3.1 client as a native macOS app for Apple Silicon and Intel Macs. The app supports NWN log discovery, character profiles, AI drafts, translation, edit recovery, and backups.

**New testers:** download `INSTALL_MACOS.md` from the release Assets and follow its first-launch, permission, and Keyboard Test steps before enabling Auto Send or AFK.

Automatic replies and AFK emotes can be sent to NWN through macOS System Events. The sender checks the foreground process before opening chat, after opening chat, and before submitting. Manual drafts are pasted without pressing Enter. Function-key hotkeys are also enabled when macOS permits them.

Grant `RoleWeaver` access in **System Settings → Privacy & Security → Accessibility**, and allow its **Automation** request for System Events. Global hotkeys may also need **Input Monitoring**. Run **Keyboard Test** with NWN open before enabling automatic or AFK sending; the test pastes an unsent line that you can cancel with Escape. These desktop permissions and actual NWN chat behavior still require live testing on a Mac.

Download the ZIP matching your Mac processor, unzip it, and move `RoleWeaver.app` to Applications. The app is ad hoc signed and not notarized; macOS may require **Control-click → Open** on first launch. Personal data is stored in `~/Library/Application Support/RoleWeaver` and is kept when the app is replaced.

This build has automated compilation and unit checks on macOS runners. Live Neverwinter Nights gameplay has not yet been verified on a Mac.
