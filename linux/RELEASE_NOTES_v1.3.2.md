# Role Weaver v1.3.2 — Linux

This maintenance release fixes a missing Guardrails AI dependency file in the
packaged Windows client. Linux behavior is unchanged; the Linux archive is
versioned v1.3.2 so all clients can use the same stable release and updater.

From v1.3.1, use **Updates → Check for Updates → Download Update → Prepare New
Folder**. Close the old client, run `bash install-linux.sh` in the prepared
folder, then run `bash start-role-weaver.sh`. Keep the old installation for
rollback and back up saved data first. See [installation](INSTALL_LINUX.md)
and [testing](TESTING_v1.3.2.md).
