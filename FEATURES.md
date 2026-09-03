# Role Weaver Features

Role Weaver is a **Neverwinter Nights roleplay client for both players and Dungeon Masters**. The same continuity engine can support a player's personal character or a DM's recurring NPC.

## For players

- Maintain a consistent voice for your own character.
- Remember relationships, promises, suspicions, goals, and unresolved stories.
- Generate multiple possible replies when you want inspiration.
- Edit every response before it becomes your character's dialogue.
- Use persistent Guidance for temporary moods, secrets, intentions, or scene tone.
- Review old conversations when returning to a storyline.
- Keep private Tell context separate from unrelated public chat.
- Filter explicit OOC conversation from AI roleplay context.

## For Dungeon Masters

- Build recurring NPCs with stable personalities and speaking styles.
- Preserve NPC relationships with individual player characters.
- Maintain lore about factions, locations, laws, religions, and events.
- Share character profiles and lore with other DMs.
- Give several DMs a common characterization baseline for the same NPC.
- Review and correct persistent memory when campaign canon requires it.
- Use Guidance to change an NPC's immediate agenda or emotional state without rewriting the permanent profile.

## Roleplay generation

- **Multiple candidate replies** — F8 generates several distinct in-character options.
- **Editable AI Draft workspace** — edit, regenerate, shorten, lengthen, clear, and paste a draft into NWN.
- **Direct NWN draft workflow** — F9 places an editable response in the NWN chat field without pressing the final Enter key.
- **Automatic response length control** — Auto, Brief, Normal, and Detailed modes.
- **Persistent Guidance** — scene direction remains active until explicitly cleared or replaced.
- **Generation timing** — shows how long the latest generation took and which model handled it.

## Character continuity

- **Persistent character memory** — durable facts are stored separately by server and portrayed character.
- **Relationship tracking** — tracks supported trust, suspicion, friendship, obligations, conflict, affection, authority, and other interpersonal state.
- **Automatic session summarization** — condenses long-running scenes into continuity summaries.
- **Conversation history viewer** — select and search past session transcripts.
- **Manual memory editing** — the human can correct relationship and memory entries.

## Context and lore

- **Lore reference files** — focused `.txt` references are retrieved when relevant.
- **Visible AI Context** — inspect the actual character instructions, memory, relationships, lore, summary, chat, and Guidance used for a reply.
- **Manual context controls** — ignore messages, pin important context, or forget older conversation.
- **IC/OOC detection** — common explicit OOC forms are excluded from generation context by default.
- **Better Tell handling** — private Tell conversations maintain separate context threads.

## Profiles and AI providers

- **Server-specific character profiles** — maintain different versions/settings for different servers or campaigns.
- **Character-specific AI settings** — provider, model, LM Studio URL, response-length preference, and candidate count can be stored per profile.
- **OpenAI, Google Gemini, and LM Studio support**.
- **Gemini fallback logic** for configured alternate models.
- **Local LM Studio option** for users who prefer local inference.

## NWN integration

- Watches the Neverwinter Nights client log in near real time.
- Parses supported chat channels and identifies the configured portrayed character.
- Uses global hotkeys for fast live RP.
- Normalizes punctuation before pasting into NWN.
- Uses Windows input methods to place editable text into the NWN chat field.

## Shared campaigns

Role Weaver can support a collaborative DM world through shared:

```text
Characters\<server>\
Lore\
```

Those files are suitable for a private campaign Git repository.

Runtime memory and history are local in the current release candidate. Role Weaver does **not** yet provide automatic multi-user/cloud synchronization of live memories.

Whether you are running the world or simply living in it, the design principle is the same:

**the human owns the character; Role Weaver helps preserve the story.**
