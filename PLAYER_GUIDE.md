# Role Weaver for Players


Before live RP, first complete **AI_PROVIDER_SETUP.md**, then create your character/NPC using **CHARACTER_PROFILE_GUIDE.md**.

Role Weaver is not only a DM tool. Any Neverwinter Nights player can use it as an **RP continuity and writing assistant for their own character**.

The goal is not to have AI play your character for you. The goal is to give you useful drafts and memory so that **you can portray your character more consistently and spend more time enjoying the scene**.

## Build a useful player-character profile

A good profile tells Role Weaver how your character tends to think and speak without trying to pre-write every possible response.

Useful sections include:

- **Personality** — temperament, strengths, flaws, emotional habits.
- **Speaking Style** — vocabulary, formality, humor, dialect, typical response length.
- **Background** — only the history that matters for present roleplay.
- **Beliefs** — principles, prejudices, loyalties, fears, moral boundaries.
- **Relationships** — important established relationships.
- **Current Goals** — what the character presently wants.
- **Secrets** — things the character knows but should not casually reveal.
- **Roleplay Rules** — boundaries on what the AI should invent or control.

The included `character_Kaelen_Marr_Player_Character.txt` is a starting example.

## During play

### F8: several possibilities

Use **F8** when you want inspiration. Role Weaver generates multiple candidate replies. Choose one, edit it, shorten it, lengthen it, regenerate it, or ignore all of them.

This works particularly well when:

- a conversation takes an unexpected turn;
- you know how your character feels but cannot find the wording;
- you want to compare a cautious, warm, humorous, or confrontational response;
- a long-running relationship has accumulated more history than you can easily recall.

### F9: fast editable response

Use **F9** when you want Role Weaver to generate a response and place it directly in the NWN chat field.

Role Weaver intentionally leaves the final Enter press to you. Read the line first. Change anything that does not sound like your character.

## Persistent Guidance

Guidance remains active until you clear or replace it. For a player, this is useful for temporary character state.

Examples:

```text
Kaelen is exhausted and unusually impatient tonight. Keep replies shorter and less playful.
```

```text
He trusts Mira, but is still hiding what happened at the ruins. Be warm without revealing the secret.
```

```text
This is a relaxed tavern scene. Allow more humor and casual conversation.
```

The permanent character profile describes **who the character generally is**. Guidance describes **how the character should be played right now**.

## Relationships and memory

Role Weaver can remember how recurring characters relate to yours: friendship, distrust, obligations, rivalry, gratitude, affection, authority, and unresolved conflict.

Review these entries occasionally. AI summaries are useful continuity aids, not unquestionable canon. If an entry misunderstands the scene, edit it.

## Lore

Lore files can help your character respond consistently to known factions, places, religions, laws, organizations, or previous events.

Only give Role Weaver information your character is allowed to use. If a lore file contains DM-only secrets and you are playing a normal character, do not place that secret in the player's accessible lore library.

## Tells and OOC

Private Tell conversations are kept in separate context threads so an unrelated public conversation is less likely to contaminate the reply.

Common explicit OOC forms such as `(( ... ))`, `// ...`, and `OOC:` are kept in history but normally excluded from reply-generation context.

## Manual context controls

The AI Context tab lets you intervene when the automatic context is not what you want.

- **Ignore / Unignore** — leave a message visible but remove it from AI generation.
- **Remember / Unremember** — pin an important message into context.
- **Forget Before Here** — discard older active conversation context.

The visible AI Context view is also useful for answering a simple question: **“Why did Role Weaver suggest that?”**

## Good player habits

Role Weaver works best when you treat it as a collaborator rather than an autopilot.

Read every response. Change wording freely. Reject drafts that are too clever, too knowledgeable, too emotional, or simply unlike your character.

Other players should still feel that they are roleplaying with **you**.

## Example folder layout

```text
Characters\
    CUSTOM\
        character_Kaelen_Marr_Player_Character.txt
Lore\
    City_of_Asterfall.txt
    Kaelen_Known_History.txt
```

For different servers or campaigns, keep separate profiles so the same character name does not accidentally inherit the wrong setting or continuity.

**Your character remains yours. Role Weaver helps you remember who they have become.**
