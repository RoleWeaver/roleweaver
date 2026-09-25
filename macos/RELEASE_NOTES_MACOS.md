# Role Weaver v1.3.1 macOS preview 1

This preview builds the Role Weaver 1.3.1 client as a native macOS app for Apple Silicon and Intel Macs. The app supports NWN log discovery, character profiles, AI drafts, translation, edit recovery, and backups.

Game input uses a clipboard handoff: generate or edit a draft, copy it, switch to Neverwinter Nights, and paste with Command+V. Global hotkeys, automatic sending, and AFK sending are unavailable in this preview. A clipboard copy is never recorded as a sent line.

Download the ZIP matching your Mac processor, unzip it, and move `RoleWeaver.app` to Applications. The app is ad hoc signed and not notarized; macOS may require **Control-click → Open** on first launch. Personal data is stored in `~/Library/Application Support/RoleWeaver` and is kept when the app is replaced.

This build has automated compilation and unit checks on macOS runners. Live Neverwinter Nights gameplay has not yet been verified on a Mac.
