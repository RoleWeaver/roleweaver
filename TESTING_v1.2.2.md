# Role Weaver v1.2.2 Stable Release Checklist

## Memory hotfix
- Open a character with conversation history.
- Open **Character Memory**.
- Press **Summarize Now**.
- Confirm the summary completes without a NameError.
- Confirm relationships/shared-with-player memory still rejects obvious non-character entities.

## Automatic world/log detection
- Start with a clean Role Weaver data directory.
- Confirm Server / Log initially shows only **Auto Detect**.
- Confirm no NWN logs are bundled with Role Weaver.
- Let Role Weaver inspect locally existing NWN logs.
- Confirm discovered worlds are added locally.
- Browse to another valid NWN log and confirm it can be parsed without requiring a bundled server profile.

## Generic profiles
- Confirm `character_Example_Player.txt` and `character_Example_NPC.txt` are present under `Characters/AUTO`.
- Confirm both can be adapted to a newly detected world.

## Distribution
- Confirm version is 1.2.2 in VERSION and the installer.
- Confirm GitHub Actions builds Installer, Portable ZIP, Neverwinter Vault ZIP, and SHA256SUMS.txt.
- Confirm there are no obsolete third-party download-site files in the release tree.
