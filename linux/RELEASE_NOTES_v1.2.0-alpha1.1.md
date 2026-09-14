# Role Weaver v1.2.0-alpha1.1 — Identity & Data Management

This staged alpha focuses on protecting persistent RP data before the Character Intelligence work in alpha2.

## New
- Multiple campaigns per server with Create, Load, Rename, and Delete controls.
- Active campaign selector in DM Cast.
- Campaign-specific NPC membership; NPC profiles can belong to multiple campaigns without being duplicated.
- Campaign deletion leaves underlying NPC profiles and personal character memory intact.
- Character identity aliases and conservative title resolution.
- Manual Add Alias and Merge Into controls in Relationships.
- Titled references such as `Reverend Mother Garcia Longhouse` can resolve to an existing `Garcia Longhouse` memory record when the match is unique.
- Memory summarizer output now passes through the same identity resolver so aliases do not create duplicate durable records.
- Player-profile mismatch warning based on the current NWN log session.
- When the detected NWN character differs from the loaded Player profile, Role Weaver offers to switch to a uniquely matching profile, keep the current profile deliberately, or cancel startup.
- NPC profiles skip the mismatch warning because DMs commonly portray NPCs while logged into another NWN character.

## Compatibility
- Existing v1.1/v1.2-alpha1 character memory is migrated in place with a new `identity_aliases` map.
- Existing alpha1 campaign folders remain valid and appear in the Campaign selector.
- Legacy alpha1 campaigns initially treat all existing NPC profiles as members until membership is changed.

## Test focus
1. Create, switch, rename, and delete campaigns.
2. Add/remove the same NPC from different campaigns.
3. Confirm deleting a campaign does not delete NPC profiles or their personal memory.
4. Talk to the same character under titled and untitled forms and verify only one durable memory record is used.
5. Test Add Alias and Merge Into on existing duplicate records.
6. Start Role Weaver with the wrong Player profile and verify the mismatch dialog.
7. Choose Keep Current Profile and confirm intentional testing still works.
8. Load an NPC profile and confirm no mismatch warning is shown.
