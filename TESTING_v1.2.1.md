# v1.2.1 Test Checklist — Automatic Server & Log Detection

Use this checklist to verify the stable v1.2.1 build before and after publishing.

## Upgrade test

- Install/run v1.2.1 over a copy of an existing Role Weaver data directory.
- Confirm the previously selected world still appears locally.
- Confirm its character profiles, memory, lore, campaign data, and DM continuity data remain available.

## Fresh-install test

- Start with no `settings.json`.
- Confirm the server/world control shows only `Auto Detect` until a world is actually discovered from local logs.
- Click **Rescan Logs** and confirm locally detected worlds populate the list.
- Confirm no bundled list of public persistent worlds appears.

## Log switching test

- Browse to several different NWN client logs.
- Confirm each recognizable world is added locally.
- Confirm the log path changes with the selected world.
- Confirm selecting a world scopes Characters, Lore, Campaigns, RoleplayRules, and RoleWeaver_Data correctly.

## Parser test

For each available log sample, verify representative lines for:

- Talk
- Whisper
- Party
- Tell
- Shout
- DM

Confirm a message written twice by NWN (`[CHAT WINDOW TEXT]` + structured copy) enters context only once.

## Live-play test

- Start Role Weaver before or during a live NWN session.
- Confirm new chat appears in context.
- Confirm speaker names and channels are correct.
- Confirm current-area tracking updates when changing areas.
- Confirm F8 creates candidates.
- Confirm F9 pastes an editable unsent reply into NWN.
- Confirm F10 behavior is unchanged.

## Failure/fallback test

- Browse to a log with no obvious world welcome line.
- Confirm Role Weaver chooses a conservative local label and remains usable when a log is selected manually with **Browse...**.
- Confirm an unfamiliar chat layout does not crash Role Weaver.

Report test results or problems to **roleweaverinfo@gmail.com** or GitHub Issues.
