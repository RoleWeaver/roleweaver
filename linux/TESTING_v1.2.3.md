# v1.2.3 acceptance checks

1. Back up existing data and install/extract into a writable location.
2. Open Recover Edits on a smaller screen. Copy text, Discard and Clear all must
   stay visible; text must scroll and shrink when resizing.
3. Select NWN2 EE and verify a live nwclientLog1.txt or nwn2client64Log1.txt under
   Temp/NWN2 EE. Follow NWN2_LOGGING.md if no file is being written.
4. Check new Talk, Party, Whisper/Tell and DM messages with the correct speaker;
   combat/script lines must not become dialogue.
5. Switch games while stopped and confirm remembered paths when switching back.
6. Check AFK's initial emote, 30-second checks and three-minute cooldown.
   Disable AFK during generation and confirm no pending emote is sent.
7. Verify recovered edits and pending summaries survive a forced client close.

Run python -m unittest discover -s tests in each platform directory.
Linux release CI also checks recovery-button visibility under Xvfb.
