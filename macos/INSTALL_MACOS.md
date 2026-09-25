# Install Role Weaver on macOS

This is a preview build of Role Weaver 1.3.1 for testing with Neverwinter Nights. The app was compiled on macOS 15 for Apple Silicon and Intel Macs. Live game input still needs tester validation.

## 1. Download the correct ZIP

1. Open the [macOS release page](https://github.com/RoleWeaver/roleweaver/releases) and select the newest **macOS preview** release.
2. Choose `RoleWeaver-v1.3.1-macOS-arm64.zip` for an Apple Silicon Mac (M-series chip), or `RoleWeaver-v1.3.1-macOS-x86_64.zip` for an Intel Mac. In **Apple menu → About This Mac**, Apple Silicon appears under **Chip** and Intel appears under **Processor**.
3. Double-click the ZIP in Downloads to extract `RoleWeaver.app`. Drag the app to **Applications**. Replace an older `RoleWeaver.app` there if prompted, after closing it. Your profiles and settings are stored separately in `~/Library/Application Support/RoleWeaver`.

## 2. Open the app the first time

Double-click `RoleWeaver.app` in Applications. This preview is ad hoc signed and not Apple notarized, so macOS may block its first launch. If you trust the ZIP you downloaded from this release, try opening the app once, then go to **System Settings → Privacy & Security**, scroll down, and choose **Open Anyway** for RoleWeaver. Confirm **Open** when macOS asks again. Apple's [app-opening instructions](https://support.apple.com/en-gb/102445) explain this step. Do not change the system-wide app security setting.

## 3. Set up Role Weaver

1. Start Neverwinter Nights and enable its client chat log. In Role Weaver, select your game version and confirm the **Server / Log** path points to the active client log. For NWN:EE, Role Weaver checks `~/Documents/Neverwinter Nights/logs` and `~/Library/Application Support/Neverwinter Nights/logs`. Use **Browse** if your game stores logs elsewhere.
2. Select or create a character profile. Configure your AI provider and API key in Role Weaver. Keep your API key private.
3. Click **Start** and confirm new game chat appears in Role Weaver's activity or conversation view.

## 4. Enable game input

1. Open **System Settings → Privacy & Security → Accessibility** and allow `RoleWeaver`. If it is not listed, add `RoleWeaver.app` from Applications. See [Apple's Accessibility instructions](https://support.apple.com/en-gu/guide/mac-help/mh43185/mac).
2. When macOS asks whether RoleWeaver may control **System Events**, choose **Allow**. If you previously denied it, review **System Settings → Privacy & Security → Automation**. See [Apple's Automation instructions](https://support.apple.com/en-mz/guide/mac-help/mchl108e1718/mac).
3. With NWN running, click **Keyboard Test** in Role Weaver. Switch to the NWN window during the countdown. The test should open chat and paste a line **without sending it**. Press **Escape** in NWN to discard the line. If the test fails, leave Auto Send and AFK off and check the activity message and permissions.
4. Once the test succeeds, use **Auto Send OFF** to enable automatic replies or **AFK OFF** to enable AFK emotes. Both modes start off each session. Use the on-screen buttons; global function-key hotkeys are disabled in this preview.

## If something does not work

- **No game log:** Select the actual log file with **Browse** and confirm NWN is writing new chat lines to it.
- **Keyboard Test cannot find NWN:** Check **Window Title Contains** in Role Weaver settings against the game's visible window or process name.
- **Permission or input error:** Recheck Accessibility and Automation for the copy of `RoleWeaver.app` in Applications, then quit and reopen the app. Run Keyboard Test again before enabling Auto Send or AFK.
- **App does not open:** Follow the **Open Anyway** step above. Do not remove macOS quarantine with a Terminal command.

For a useful [bug report](https://github.com/RoleWeaver/roleweaver/issues/new/choose), include your Mac's chip, macOS version, NWN edition, which step failed, and the Role Weaver activity message. Remove API keys, private chat, and character or campaign details before sharing screenshots or logs.
