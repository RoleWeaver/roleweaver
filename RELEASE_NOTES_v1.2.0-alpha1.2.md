# Role Weaver v1.2.0-alpha1.2

Identity verification hotfix for the v1.2 DM/campaign alpha.

## Fixed

- Player profiles now use the NWN log's `Messages for:` session header as the primary active-character identity source.
- Selecting a Player profile performs the mismatch check immediately, rather than waiting only for Start.
- Start performs the check again before the bot begins collecting RP data.
- NPC profiles remain exempt because DMs commonly portray an NPC while logged into another NWN character.

When a mismatch is found, Role Weaver still allows the user to switch to the detected character's matching profile, deliberately keep the selected profile, or cancel.
