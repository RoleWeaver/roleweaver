# Role Weaver v1.2.0-alpha5 — Adaptive Characters

## New
- Correction Learning learns recurring style preferences from AI drafts the player edits and actually sends in NWN.
- Draft-to-final correction pairs are captured conservatively; unrelated manually typed lines are not treated as corrections.
- New Adaptive tab shows learned correction preferences and Character Development proposals.
- Character Development is never automatic. Proposals require explicit player approval before affecting AI context.
- Rejected proposals are remembered to reduce repeated suggestions.
- Approved development can be removed without modifying the original character profile.

## Safety / authority model
The explicit character profile remains authoritative. Correction learning is soft style guidance. Development proposals cannot alter portrayal until approved by the player.
