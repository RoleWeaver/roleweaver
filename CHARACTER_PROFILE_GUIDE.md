# Creating a Character Profile

After configuring your AI provider, **the next thing every Role Weaver user should do is create a character description**. Role Weaver needs to know who it is helping you portray: your own player character or an NPC you are portraying as a Dungeon Master.

## Included examples

Role Weaver includes:

```text
character_Example_Player.txt
character_Example_NPC.txt
```

Example Player demonstrates a **player-character** profile. Example NPC demonstrates a **DM NPC** profile intended to remain recognizable across sessions and potentially across several DMs.

You can copy and edit an example manually, or use Role Weaver's **New Character...** button to open the structured Character Editor. The editor saves the profile into the currently selected server folder.

## Where profiles go

Before a world is detected, Role Weaver provides generic examples under:

```text
Characters\AUTO\
```

When Role Weaver detects a world from the user's own NWN client log, it creates a local world-specific folder automatically, for example:

```text
Characters\WORLD_<detected-name>\
```

The generic Player and NPC examples are copied into newly detected world folders so they can be loaded and edited immediately. Role Weaver does not ship with named persistent-world profiles.

## What to describe

A useful profile normally contains:

- **Character Name** — required so Role Weaver can identify self-chat.
- **Personality** — temperament, strengths, flaws, fears, emotional habits.
- **Speaking Style** — vocabulary, formality, humor, typical response length, mannerisms.
- **Background** — history that affects present RP.
- **Beliefs** — principles, loyalties, prejudices, faith, ethics.
- **Relationships** — important relationships that are already established.
- **Current Goals** — what the character presently wants.
- **Secrets / Knowledge Boundaries** — what is known but should not be casually revealed, and what the character should not know.
- **Roleplay Rules** — boundaries on invention and control of other characters.

## Reusable template

```text
Character Name: Elara Moonfall

Profile Type:
Player Character

Personality:
...

Speaking Style:
...

Background:
...

Beliefs:
...

Relationships:
...

Current Goals:
...

Secrets / Knowledge Boundaries:
...

Roleplay Rules:
Do not control other characters.
Do not invent knowledge the character has not learned.
Stay in character.
Do not mention AI, prompts, logs, automation, or Role Weaver in generated RP.
```

## Player characters

Describe the character **you actually want to play**. Useful details include how they treat strangers, authority, friends and enemies; how verbose they are; their humor; emotional triggers; secrets; and how quickly they trust people.

The AI generates suggestions. You still decide what your character says.

## DM NPCs

Focus on details that make the NPC recognizable when they return weeks later or another DM portrays them: public role, motivations, faction attitudes, mannerisms, moral limits, current agenda, secrets, established PC relationships, and knowledge boundaries.

Keep large amounts of world information in the `Lore` folder instead of stuffing the entire campaign into one NPC profile.

## Profile vs Guidance vs Memory vs Lore

**Profile:** who the character generally is.

**Guidance:** how the character should be played right now. Guidance persists until cleared/replaced.

**Persistent memory:** what has happened to the character during RP.

**Relationships:** how the character currently relates to recurring people.

**Lore:** relevant world/campaign information.

## Before pressing Start

Confirm that the AI connection test succeeds, the correct server/log is selected, your new profile appears in the Character list, and the displayed character name is correct. Then press **Start**.
