# Unfinished edit and pending summary recovery

Both desktop clients now retain edits and pending summary work across restarts, in addition to automatic crash backups.

## Recovering unfinished edits

Only user changes in Guidance, character-editor text fields, Lore and AI Draft are captured locally. Other controls, entries, relationships and campaign/memory editors are excluded. The collector binds directly to these editors, so internal Tk popup events cannot produce widget-path errors. Writes are scheduled 750 milliseconds after capture, even while typing continues; a busy UI or disk errors can delay them. Changes are also flushed when focus leaves a field or the client closes normally. If flushing fails on close, the client asks before abandoning those changes.

Select **Recover Edits** in the settings sidebar when needed; there is no startup recovered-edits popup. Select a saved field, review its text, click **Copy text** (copies highlighted text, or the whole displayed edit if nothing is highlighted), then paste it into the intended editor. Recovery does not overwrite files or send text to NWN or an AI provider. Each field is a separate record, with window, field, server/character context and a timestamp. A form with several changed fields can have several records. Use **Clear all** to remove past recovered edits, including pending captured edits, without changing saved profiles or lore. Saved edits otherwise remain in the list until explicitly discarded; this is a recovery history, not an automatic replacement of the original form.

Drafts are kept in `RoleWeaver_Data/Recovery_Drafts`. They are private plaintext JSON and included in backups. There is no automatic pruning of recovered edits. A crash before the next capture/write can still lose the last fraction of a second of typing. Disk-full errors appear in Activity and writes are retried while the app remains open.

## Pending AI summaries

When memory is enabled, accepted IC events are written to a per-character `pending_summaries.json` journal before they are queued for summarization. OOC events are excluded. Starting the same character with a configured AI provider automatically resumes queued work. **Summarize Now** also retries it.

Events remain durable while the AI request is running. Once a valid response arrives, it is cached locally before its memory changes are applied. A failed or interrupted application can therefore reuse the response. The result is applied to a copy of the latest memory so a partial merge cannot leak into later saves.

The memory JSON atomically records the result, running summary and completed batch ID. The queue is acknowledged afterward. If the process ends between those steps, startup recognizes the already-completed batch and clears it without applying it again. The separate running-summary text file is now a convenience copy; the memory JSON is authoritative.

New events arriving during a request remain queued separately. Normal desktop shutdown may interrupt an AI request, but its queued events are retained for the next Start. If the response had not yet been received and saved, the request may need to run again and incur another provider charge.

Automatic startup recovery preserves newer readable edit records and pending journals when restoring an older snapshot. Manual backup restoration still restores the selected archive's matching files. Its pre-restore recovery ZIP preserves the files it replaces.

## Installing this update

These are source packages. Close the client and keep a copy of your installation before updating. Replace all seven Python files together using the package for your platform:

- `nwn_ai_bot.py`
- `nwn_ai_gui.py`
- `roleweaver_backup.py`
- `roleweaver_storage.py`
- `roleweaver_crash.py`
- `roleweaver_pending.py`
- `roleweaver_drafts.py`

Keep personal settings, profiles, lore, campaigns and memory folders. Do not overwrite them with the bundled examples. Use the usual platform launcher. Windows executable installations need a rebuilt executable; placing these source files beside an old executable does not update it.

## Validation and limitations

The Windows source passes 51 tests (plus one Linux-only test skipped) and the Linux source passes 79 on the Windows host. Tests cover interrupted application, completion before queue acknowledgment, cached-response reuse, concurrent requests, events arriving during a request, atomic-save failures, draft capture during continuous typing, API-key exclusion and preservation of newer recovery work during a snapshot restore. Source compilation passes.

Full desktop/gameplay acceptance remains untested here because the bundled Tk runtime lacks its Tcl files and no usable Linux desktop is available. Existing X11/Wayland adapters are retained. These are unreleased source changes; existing release downloads have not been rebuilt.

## Development status

The maintainer confirmed the recovery and feedback-fix tests work on Windows and Linux. Further features will be added before creating the next distribution. Automated tests ran on the Windows host; that does not establish exhaustive native Linux desktop or gameplay coverage.
