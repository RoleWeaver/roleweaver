# Public Release Checklist

Before publishing Role Weaver on GitHub:

- [ ] Choose and add a software license.
- [ ] Replace any placeholder repository links in documentation.
- [ ] Confirm no API keys, personal log paths, private character profiles, or conversation histories are committed.
- [ ] Test a clean install on a Windows machine or VM.
- [ ] Test F8/F9/F10 with NWN:EE.
- [ ] Test OpenAI, Gemini, and LM Studio with currently supported models.
- [ ] Confirm the splash image and taskbar icon display correctly.
- [ ] Verify `requirements.txt` installs in a fresh virtual environment.
- [ ] Tag a version such as `v0.9.0`.
- [ ] Create a GitHub Release ZIP.
- [ ] Add screenshots and a short GIF/video showing the F8/F9 workflow.
- [ ] Document known limitations, especially local-only memory synchronization.
- [ ] Consider adding a signed standalone Windows build in a later release.

## Player + DM messaging

- [ ] GitHub description says Role Weaver is for **players and DMs**.
- [ ] Screenshots show both a player-character workflow and a DM/NPC workflow.
- [ ] Release notes link to both `PLAYER_GUIDE.md` and `DM_GUIDE.md`.
- [ ] Test both included example profiles on a clean installation.
- [ ] Avoid describing Role Weaver as an autonomous player or autonomous DM.
