# Automatic crash protection and recovery

Automatic protection is enabled when you launch the updated desktop client. There is no setup switch.

## What happens automatically

- Settings, memory, profiles, lore, campaigns, guidance and conversation history use temporary files, flush them to disk, then replace the saved file. An interrupted replacement leaves the prior complete file available. Memory/summary saves and backups share a lock so a backup cannot run halfway through that save operation.
- A backup is created after startup, every five minutes while the client is open, and on normal exit. Ten automatic ZIPs are retained in `Backups/Automatic`. Old automatic copies are pruned only after a replacement backup passes validation. Manual backups and pre-restore recovery copies are not pruned.
- Successful automatic backups are silent; the Activity panel reports backup errors. A full disk or other backup failure retains earlier copies. A failed final backup leaves the session marked unclean for the next launch.
- A session marker and an operating-system lock detect unexpected termination and prevent another updated desktop client from using the same installation at the same time. The lock is released by the OS after a crash; the marker survives.
- Before loading settings, startup checks saved JSON. After an unclean exit or invalid saved JSON, it offers the newest automatic archive whose checksums and JSON validate, skipping damaged archives. You can restore, keep current data if readable, or exit. Recovery requires confirmation; it never silently replaces current files.
- Recovery first saves current files in a `Backups/before-restore-<id>.zip`. Files absent from the chosen archive are retained. If a restore write fails, touched files are rolled back. If saved data is unreadable and cannot be recovered, startup stops instead of loading defaults over it.

## Manual backup and restore

Use **Settings > Backup** before pressing Start. After a session, restart the client before using these manual controls. Automatic backups continue during sessions.

Manual ZIPs include saved settings, characters, lore, campaigns, rules, persistent memory, conversation history, legacy character prompt and next guidance. Manual restore validates the archive, preserves a recovery copy, replaces matching files and closes the client; reopen it afterward. Recovery copies use the same merge behavior: they do not delete files added after the original backup.

Archives are not encrypted and can contain private roleplay data and personal paths. Environment variables and API keys entered only in the provider field are not included. Each backup is limited to 1 GiB uncompressed and 20,000 files. Linked files, unsafe/duplicate paths and checksum mismatches are rejected. Checksums verify integrity, not authenticity.

## What this protects

This protects saved files against interrupted writes and provides recent copies for recovery. Unfinished user edits are now autosaved, and pending AI summaries are journaled; see [Edit and summary recovery](EDIT_SUMMARY_RECOVERY.md). Text not yet captured by the edit autosave and AI responses not yet received can still be lost. Restoring a five-minute backup may discard more recent saved changes; keep current files when they are intact. A process crash between separate file replacements is not a whole-application transaction; startup recovery can return matching files to a snapshot.

Backups share the application's drive, so continue making private backups on another drive for hardware failure protection. Do not run an old client or the console bot against the same installation while the updated desktop client is open; those entry points do not acquire the desktop session lock. Close external editors before manual restoration. Protection does not guarantee recovery from hardware failures or logically incorrect but valid JSON.

## Update an existing source installation

Close the client and keep a copy of its folder. Replace these seven application files together, using the package for your platform:

- `nwn_ai_bot.py`
- `nwn_ai_gui.py`
- `roleweaver_backup.py`
- `roleweaver_storage.py`
- `roleweaver_crash.py`
- `roleweaver_pending.py`
- `roleweaver_drafts.py`

Keep your settings, Characters, Lore, Campaigns, RoleplayRules and RoleWeaver_Data folders. Do not overwrite personal data with the package's generic examples. Use the normal platform launcher. Windows executable installations need a rebuilt executable; copying Python modules beside an older executable does not update it.

If startup reports invalid data and you only have a manual backup, close all clients and use the standard-library recovery module from the installation directory, then relaunch:

```python
from pathlib import Path
from roleweaver_backup import restore_backup
restore_backup(Path.cwd(), Path("/path/to/your-backup.zip"))
```

## Validation

Run `python -m unittest discover -s tests -v` and `python -m py_compile nwn_ai_bot.py nwn_ai_gui.py roleweaver_backup.py roleweaver_storage.py roleweaver_crash.py` from the application directory.

Crash tests include a real subprocess terminated before replacing a saved file, crash-marker survival, process-lock release, second-process rejection, injected disk-write failures, retention, a periodic worker, corrupt-archive fallback, startup recovery and preservation of damaged data. GUI callbacks are tested with dialogs mocked.

## Development status