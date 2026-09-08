# Role Weaver v1.2.2 Distribution Validation

This source tree was prepared as the stable v1.2.2 distribution.

Validation performed before packaging:

- `VERSION` is 1.2.2.
- Inno Setup default application version is 1.2.2.
- Python source compiles successfully.
- Character Memory `Summarize Now` uses `is_likely_relationship_character(...)`; the obsolete `is_valid_relationship_entity` call is absent.
- New installs use Auto Detect rather than bundled named persistent-world profiles.
- Generic Player and NPC example profiles are included under `Characters/AUTO`.
- No NWN client/server log samples are bundled.
- No named persistent-world compatibility names are present in source or current documentation.
- Neverwinter Vault distribution documentation is included.
- Obsolete third-party download-site packaging is absent.
- GitHub Actions is configured to create installer, portable ZIP, Neverwinter Vault ZIP, and SHA256 checksums.
- Python cache/compiled files are excluded from the distribution.
