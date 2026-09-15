# AFK mode (v1.2.3)

F10 or the AFK button toggles Away From Keyboard for the selected character.
AFK starts off each session. It sends one short LLM-generated emote on activation,
then checks for attention every **30 seconds**. New incoming Tells or IC Talk,
Whisper, Party or DM messages mentioning the character's full name or first name
request another emote, with a **three-minute minimum interval** between sends.
Unrelated chat and the character's own messages do not trigger replies.
Name matching is approximate: nameless questions may be missed.

AFK pauses normal automatic replies. Switching it off restores the previous mode
and discards any AFK response still being generated. Stop also cancels pending
responses; F6 pauses AFK sending. Emotes do not answer questions or make decisions.
No conversation text is sent to the AFK generator, only the character profile.
Emotes use the existing NWN chat delivery mechanism and currently selected chat
channel; they do not automatically target the sender of a Tell.

Windows and Linux X11 support automatic delivery. Linux Wayland retains manual
paste only, so AFK is unavailable there. Linux global hotkeys require X11.

## Manual checks on Windows and Linux X11

1. Start the client, activate AFK, and confirm one short emote reaches NWN.
2. Have another character mention your character by name. Confirm no repeat
   before three minutes and a response on the next 30-second check thereafter.
3. Leave unrelated chat running: no extra AFK emotes should appear.
4. Turn AFK off while the LLM is generating: that response must not be sent.
5. Repeat using Stop, and verify restarting the client leaves AFK off.
6. Verify normal F8/F9 behavior after turning AFK off.

Included in v1.2.3.
