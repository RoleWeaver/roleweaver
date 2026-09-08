# Automatic World and Log Detection

Role Weaver v1.2.1 does **not** ship with a named persistent-world server list.

Instead, it discovers worlds locally from the Neverwinter Nights client logs on the user's own computer. This keeps Role Weaver server-neutral while still isolating character profiles, lore, campaigns, rules, and memory by world.

## How detection works

Role Weaver scans likely NWN client logs and looks for generic signals such as:

- explicit `Welcome to ...` login text;
- early onboarding greetings that identify a world;
- area-entry messages such as `*Now Entering ...*` or `<< You have entered the area: ... >>`;
- the structure of chat records written by NWN.

If an explicit world name is not available, Role Weaver uses a conservative local label derived from the log, such as the root name of the current area. The detected label can remain entirely local.

## Adaptive log parsing

Role Weaver no longer chooses a parser from a named-server profile. It detects the dominant log representation and stores that information with the local world profile.

Recognized chat layouts include:

```text
[account-id] Character Name: [Talk] Message
Character Name: [Whisper] Message
[Talk] Character Name: Message
Character Name [Party]: Message
[CHAT WINDOW TEXT] [timestamp] Character Name: [Tell] Message
```

When NWN writes both a human-readable `[CHAT WINDOW TEXT]` copy and a structured copy of the same message, Role Weaver prefers the structured record so the conversation is not duplicated.

Supported channels are Talk, Whisper, Party, Tell, Shout, and DM.

## Local profiles

Detected worlds are saved in `settings.json` under `discovered_servers`. A local profile stores only information needed by Role Weaver, such as:

- display name;
- log-file path;
- detected parser format;
- last-seen timestamp.

Role Weaver does not contact a persistent-world server to perform detection and does not download a public compatibility list.

## Manual fallback

If automatic detection cannot identify a useful world or log format, use **Browse...** to choose the desired NWN log file directly. The adaptive parser remains available for unrecognized layouts.
