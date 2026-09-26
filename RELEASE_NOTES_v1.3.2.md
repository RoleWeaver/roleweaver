# Role Weaver v1.3.2

This maintenance release fixes Guardrails AI loading in the packaged Windows
client. In v1.3.1, the Windows executable could show **DEGRADED** on the
Guardrails & Usage tab because a grammar data file from a Guardrails AI
dependency was missing. The v1.3.2 build includes that file and checks the
finished executable before publishing.

The PG policy defaults, usage charts, translation workflow, and player control
over edited drafts are unchanged. The Linux package is versioned v1.3.2 for
consistent updates, with no Linux behavior change.

## Update from v1.3.1

Open **Updates**, choose **Check for Updates**, then **Download Update**.
Installed Windows copies can launch the verified Setup installer. Windows
portable and Linux copies prepare a fresh folder with copied saved data; the
old installation remains available for rollback. Back up your data and stop
the active session first. On Linux, run `bash install-linux.sh` from the new
folder before starting it. See [Updates](UPDATES.md) and
[installation](INSTALLATION.md).

After updating on Windows, open **Guardrails & Usage → Overview** and confirm
it reports Guardrails AI active, not degraded. The shipped fallback policy in
v1.3.1 still applied policy rules when the dependency was unavailable, but it
did not provide an active Guardrails AI backend.

See the [player guide](PLAYER_GUIDE.md), [DM guide](DM_GUIDE.md), and
[acceptance checks](TESTING_v1.3.2.md).
