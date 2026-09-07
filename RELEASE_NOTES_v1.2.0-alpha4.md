# Role Weaver v1.2.0-alpha4 — Continuity Tools

This staged test build adds long-horizon continuity management.

## New
- Continuity tab with resizable Story Threads, Promises & Commitments, and Event History panes.
- Manual Add/Edit/Delete controls with stable record IDs.
- Thread states: Active, Waiting, Resolved, Abandoned.
- Commitment states: Active, Waiting, Fulfilled, Cancelled, with due/direction fields.
- Automatic memory summarization can learn significant continuity events and commitments.
- Manual continuity records are authoritative and preserved.
- Relevance-ranked prompt retrieval prioritizes active commitments and unresolved threads; older resolved history is returned only when relevant/high importance.
- Private continuity is excluded from public context and can return during private Tell context.
- Existing alpha3.1 character intelligence, identity protection, and parser fixes are preserved.

## Testing focus
Create a promise and an unresolved thread, play several unrelated interactions, then return to the relevant NPC/topic and inspect AI Context. The active/relevant continuity should return without dumping the entire event history.
