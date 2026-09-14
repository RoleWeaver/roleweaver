# Role Weaver — Linux development source

This directory contains the Linux client with the tested backup, crash recovery, edit recovery, pending-summary and feedback fixes. It preserves the Ubuntu Wayland manual-paste mode and the X11 input backend.

These are unreleased source changes. The existing linux-v1.2.2-ubuntu1 release archive has not been replaced. More features will be added before the next distribution.

From a checkout, run `cd linux`, follow [INSTALL_LINUX.md](INSTALL_LINUX.md), then run `bash start-role-weaver.sh`. This is a self-contained client directory; its settings and user data remain here. Keep personal data when updating.

Read [backup/recovery](BACKUP_RECOVERY.md), [edit/summary recovery](EDIT_SUMMARY_RECOVERY.md), and [acceptance checks](FEEDBACK_FIXES.md). The repository-wide change history is in [../CHANGELOG.md](../CHANGELOG.md).

For tests, run `python -m unittest discover -s tests -v` from this directory. The top-level Linux smoke workflow runs the client from linux/ and can be dispatched manually; it does not publish a release.
