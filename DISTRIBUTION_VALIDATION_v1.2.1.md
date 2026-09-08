# Role Weaver v1.2.1 Distribution Validation

This distribution was prepared as the stable v1.2.1 source package.

Validated before packaging:

- Python source compiles and parses successfully.
- The built-in world selector contains only **Auto Detect** on a clean installation.
- Discovered worlds are added locally from the user's own NWN client logs.
- The distribution contains no bundled NWN client logs or runtime memory data.
- The distribution contains no named persistent-world compatibility profiles.
- Source code and documentation were scanned for references to previously bundled named persistent worlds.
- Two generic starter character profiles are included: one Player and one NPC.
- Generic starter profiles are copied into newly detected world folders when needed.
- VERSION and installer version are both 1.2.1.
- The publishing script replaces the GitHub working tree before commit so obsolete files from earlier releases are removed rather than left behind.
