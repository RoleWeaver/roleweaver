# Role Weaver updates

The **Updates** tab checks the latest stable GitHub release shortly after startup.
You can also press **Check for Updates** at any time. Development checkpoints and
prereleases are excluded. Role Weaver compares the release version with its own
packaged version; it does not update from an arbitrary branch or commit.

When a newer release is available, **Download Update** saves the platform asset
under `Downloads/RoleWeaver Updates`. The app downloads the release's published
SHA-256 manifest, verifies the complete download, and only then offers it for
installation. A checksum mismatch leaves the previous downloaded file alone.

On Windows installations made with the Role Weaver Setup executable, the app
offers to close and launch the verified installer. Stop the current Role Weaver
session first. The installer updates program files but does not replace existing
files in the Characters, Campaigns, Lore, or RoleplayRules directories. Settings
and runtime data are not bundled into the installer.

Portable Windows builds, developer checkouts, and Linux installations download
the portable ZIP or Linux archive. Press **Prepare New Folder**, choose a parent
folder outside the current installation, and Role Weaver will extract the new
program and copy the saved data supported by its backup system. This includes
settings, character and campaign profiles, lore, roleplay rules, draft guidance,
and RoleWeaver_Data. The old installation remains untouched for rollback.
Existing destinations are never overwritten. Archive paths, links, file counts,
expanded size, and the included VERSION file are checked before publishing the
new folder. If copying data fails, the unfinished folder is removed.

On Linux, close the old client, open a terminal in the prepared folder, then run
`bash install-linux.sh` to create a fresh virtual environment, followed by
`bash start-role-weaver.sh`. On portable Windows, close the old client and run
`RoleWeaver.exe` from the prepared folder. Existing backup ZIPs are not copied;
they remain in the previous installation. Do not extract an archive over the
current folder. Fully unattended Linux dependency installation and in-place
portable updates are not part of this stage.

The update check contacts GitHub over HTTPS. It does not send profiles, chat,
settings, or API keys. SHA-256 detects corrupted or mismatched downloads, but is
not a separate signature from GitHub's release publishing account.
