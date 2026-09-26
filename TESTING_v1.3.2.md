# v1.3.2 acceptance checks

1. Verify root, Linux, and Python package versions are 1.3.2. Check release
   asset names and both SHA-256 manifests.
2. The Windows build must contain
   `rfc3987_syntax/syntax_rfc3987.lark`. Run its packaged Guardrails smoke
   check before archiving; a source-venv check alone does not catch this bug.
3. Launch Windows Setup and portable v1.3.2. In **Guardrails & Usage →
   Overview**, confirm Guardrails AI is active, not degraded. Exercise a
   normal generated reply and confirm policy/usage reporting still works.
4. From installed and portable Windows v1.3.1, use **Updates** to download the
   v1.3.2 asset with checksum verification. Check Setup or fresh-folder
   handoff and preservation of settings, characters, campaigns, and memory.
5. Run root and Linux-layout tests, Ruff, source-integrity guard, package build,
   native Linux CI smoke, and update rehearsal. Linux behavior is unchanged,
   but verify its archive and version match the release.

Use disposable or backed-up profiles. Never upload private logs or API keys.
