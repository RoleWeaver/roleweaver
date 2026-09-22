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

Portable Windows builds, developer checkouts, and Linux installations currently
stage the verified package but do not overwrite their running installation.
Close Role Weaver and install or extract the new version into a **fresh folder**;
then move your personal data or restore a backup. Do not extract an archive over
the current folder. This is the first update stage; unattended in-place updates
for portable and Linux layouts need a dedicated data-migration mechanism.

The update check contacts GitHub over HTTPS. It does not send profiles, chat,
settings, or API keys. SHA-256 detects corrupted or mismatched downloads, but is
not a separate signature from GitHub's release publishing account.
