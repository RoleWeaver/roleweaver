# Role Weaver for Dungeon Masters


Before live RP, first complete **AI_PROVIDER_SETUP.md**, then create your character/NPC using **CHARACTER_PROFILE_GUIDE.md**.

Role Weaver is designed for both ordinary players and DMs. This guide focuses specifically on the DM side: recurring NPCs, campaign continuity, shared lore, and collaborative portrayal across a DM team.


## The goal

Role Weaver is most useful when an NPC needs to feel like a **person with continuity**, not a disposable dialogue generator.

A DM still decides what the character wants, what is canon, and whether a generated line fits the scene. Role Weaver's job is to keep useful context close at hand and reduce the cognitive burden of remembering dozens of relationships, promises, names, and prior conversations.

## Recommended NPC profile design

For major recurring NPCs, include:

- Name and role.
- Personality and emotional tendencies.
- Speaking style and vocabulary.
- Background the NPC actually knows.
- Beliefs and values.
- Current goals.
- Important secrets, clearly marked so they are not revealed casually.
- Known relationships.
- Boundaries: facts or actions the AI should never invent.

Avoid writing the entire campaign encyclopedia into a character profile. Put world information in the Lore folder instead.

## Shared NPCs in a multi-DM campaign

A practical pattern is:

```text
Characters    CUSTOM        character_Captain_Veyra.txt
        character_Archivist_Meran.txt
Lore    City_of_Asterfall.txt
    Royal_Court.txt
    Merchant_Houses.txt
```

Store those shared files in your private campaign Git repository.

When another DM needs to portray Captain Veyra, they use the same profile and lore. That creates a common characterization baseline while allowing the current DM to add scene-specific Guidance.

### Suggested DM workflow

Before a scene, review the NPC's relationship/memory entry and relevant lore. Put any temporary direction in Guidance, for example:

> Veyra suspects the party is lying. Remain courteous, but do not reveal that she already spoke to the magistrate.

During the scene, use F8 when you want several alternatives and F9 when speed matters. Review the AI Context tab whenever a response feels surprising.

After the scene, correct any relationship or memory entry that the AI summarized poorly. Human-edited campaign canon should take precedence over generated interpretation.

## Guidance as a roleplay mode

Guidance persists until cleared, so it works well as a scene-level roleplay mode without a separate preset system.

Examples:

```text
This is a tense interrogation. Speak briefly, ask pointed questions, and reveal as little as possible.
```

```text
The character is relaxed among old friends. Allow warmer humor and longer responses.
```

```text
Keep the NPC focused on the missing caravan. Do not get pulled into unrelated tavern banter.
```

Clear Guidance when the scene or emotional state changes.

## Lore practices for a DM team

Prefer many focused files over one enormous lore dump. Use canonical names in filenames because Role Weaver considers the filename while deciding what is relevant.

Good:

```text
Lore\Temple_of_the_Dawn.txt
Lore\House_Veyran.txt
Lore\Red_Market_Incident.txt
```

Less useful:

```text
Lore\everything.txt
```

An `always_` file should be genuinely universal: campaign tone rules, immutable world constraints, or shared RP conventions.

## What should be shared between DMs?

**Good candidates for Git:**

- character prompt files,
- Lore files,
- curated campaign documentation,
- intentionally reviewed relationship/memory exports if your group decides to share them.

**Usually keep local:**

- API keys,
- `settings.json`,
- raw conversation history,
- unreviewed summaries,
- personal log paths.

Role Weaver does not currently merge two DMs' memory stores automatically. Treat memory synchronization as a deliberate campaign-management operation rather than assuming simultaneous cloud state.

## Maintaining canon

The most reliable hierarchy is:

1. DM-established canon and campaign documents.
2. Curated Lore files.
3. Character profile.
4. Human-reviewed persistent memory/relationships.
5. Recent conversation context.
6. AI-generated interpretation.

If a generated answer conflicts with higher-level canon, edit the draft and fix the relevant memory or lore source.
