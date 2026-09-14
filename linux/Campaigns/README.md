# Campaigns

Role Weaver stores campaign-level DM continuity here.

Runtime structure:

`Campaigns/<server>/<campaign>/campaign_metadata.json`

`Campaigns/<server>/<campaign>/campaign_memory.json`

Campaign metadata contains the campaign name, description, and Current Situation. Campaign memory can contain shared campaign continuity, DM-only notes, NPC membership, ordered Story Beats, objectives/open questions, important locations, player/party DM notes, and an editable Session Log.

`shared_memory` may be included in character AI context where appropriate. `dm_notes` and Campaign Manager planning records are DM-facing and do not modify Player Knowledge.

Campaign Packs can be exported/imported from the **DM Cast** tab. Treat exported packs as potentially private because they may contain NPC memories, DM notes, secrets, and conversation-derived continuity.
