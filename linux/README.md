# Role Weaver 1.3.1 — Linux

Role Weaver supports all editions of Neverwinter Nights (NWN) and Neverwinter Nights 2 (NWN2), including Original NWN, Diamond, both Enhanced Editions, and NWN2 with Client Extender. Available input features depend on the platform; see [game setup](GAME_VERSIONS.md).

## Multiplayer Server Notice

Multiplayer servers have different policies on AI-assisted tools and generated content. **Always check and follow server rules before using Role Weaver**, particularly its text-generation features.

Role Weaver also provides character memory, relationship tracking, profiles, and other features that remain useful without generated dialogue, but still ensure to follow server policies.

Self-contained source client with recovery, AFK and game selection.
In a checkout, first cd linux. In the Linux release archive, the extracted folder
is already the client root. Follow [INSTALL_LINUX.md](INSTALL_LINUX.md), then run
bash install-linux.sh and bash start-role-weaver.sh. X11 supports automatic input;
Wayland uses manual paste.

Read [release notes](RELEASE_NOTES_v1.3.1.md), [game selection](GAME_VERSIONS.md),
[NWN2 logging](NWN2_LOGGING.md), [AFK](AFK_MODE.md) and [testing](TESTING_v1.3.1.md).
Keep personal data and backups when updating.

For code contributions, use the repository checkout or the release's
`RoleWeaver-Developer-vX.Y.Z.zip`, not this runnable Linux archive. The complete
source package includes both platform clients, shared contracts, tests and the
root `DEVELOPMENT.md` and `ARCHITECTURE.md` guides.
