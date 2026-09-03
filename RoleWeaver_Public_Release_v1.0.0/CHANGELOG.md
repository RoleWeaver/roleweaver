# Changelog

All notable public changes to Role Weaver are documented here.

## 1.0.0 — Initial public release

### Roleplay
- AI-assisted Neverwinter Nights: Enhanced Edition roleplay for players and Dungeon Masters.
- Character profiles with personality, speaking style, background, beliefs, relationships, goals, secrets, and roleplay rules.
- Persistent player Guidance for steering replies without exposing that guidance in-character.
- Multiple AI draft candidates and editable drafts.
- F9 workflow that generates and pastes an unsent reply into NWN for review.
- Automatic reply mode for users who explicitly enable it.

### Memory and context
- Persistent character memory and rolling session summaries.
- Relationship and attitude records for characters encountered during play.
- Separate private Tell conversation context.
- IC/OOC filtering.
- Manual context controls for ignoring, remembering, and forgetting conversation material.
- Conversation history viewer.
- AI Context view showing the roleplay material used for generation.

### World support
- Server-specific character profiles.
- Server-specific lore folders and lore editor.
- Server-specific response rules.
- Included profiles for Custom/Other, The Dragon's Neck, Arelith, Ravenloft: Prisoners of the Mist, Cormyr and the Dalelands, Star Wars: Legends of the Old Republic, and Haze: Saltborne.

### AI providers
- Google Gemini.
- OpenAI.
- LM Studio for local models.
- Provider-aware default model switching.
- Gemini fallback behavior when an eligible model is unavailable.

### Windows distribution
- Self-contained Windows executable built with PyInstaller.
- Standard Windows installer built with Inno Setup.
- Portable Windows ZIP.
- Automated GitHub Actions build and release workflow.

### Recent reliability fixes
- Improved NWN foreground/focus handling for F9/manual draft paste.
- Scan-code keyboard injection is the default for NWN.
- Manual drafts remain on the clipboard as a fallback.
- Relationship tab populates encountered characters immediately.
- Fixed relationship-memory saving.
- Fixed first provider-switch model synchronization.
