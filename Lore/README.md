# Role Weaver Lore References

Place plain-text `.txt` lore/reference files in this folder.

Role Weaver scores the current conversation against the filenames and contents,
then adds up to a few relevant lore files to the AI context automatically.

Examples:
- `Ilmater.txt`
- `Cordor.txt`
- `Temple_of_Saint_Lenore.txt`
- `House_Rivorndir.txt`

Tips:
- Use clear filenames containing important names/topics.
- Keep each file focused on one subject.
- Prefix a file with `always_` if it should always be included whenever Role
  Weaver generates a reply, for example `always_server_rules.txt`.
- The AI Context tab shows exactly which lore references were included in the
  latest reply-generation request.
