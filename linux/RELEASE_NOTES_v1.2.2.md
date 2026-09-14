# Role Weaver v1.2.2

Role Weaver v1.2.2 is a stable maintenance and distribution release based on the tested v1.2.1 Automatic Server & Log Detection build.

## Fixed
- Fixed **Character Memory → Summarize Now** failing with `NameError: is_valid_relationship_entity is not defined`.
- The memory summarizer now uses the current validated relationship-character logic when processing information shared with players.

## Distribution changes
- Added a dedicated **Neverwinter Vault** distribution package and retired the previous third-party download-site package.
- GitHub Actions now builds `RoleWeaver-NeverwinterVault-v1.2.2.zip` in addition to the normal installer and portable ZIP.
- Added Neverwinter Vault README and submission documentation.
- Removed obsolete third-party download-site documentation and packaging.

## Server/log behavior
- New installations start with **Auto Detect** rather than a bundled named-server list.
- Worlds are discovered locally from the user's own NWN logs.
- No NWN server logs are included in the distribution.
- Generic Player and NPC example profiles are available for use on any detected world.
- The source and current documentation contain no named persistent-world compatibility profiles.

## AI providers
Role Weaver supports Google Gemini, OpenAI, and local models through LM Studio.

Repository: https://github.com/RoleWeaver/roleweaver
