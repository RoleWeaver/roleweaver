# Role Weaver v1.2.0-alpha5.1 — Relationship Entity Validation

This hotfix prevents knowledge/continuity phrases from being incorrectly created as characters in Relationships.

## Changes
- Adds a conservative validation gate for LLM-created relationship, person-memory, and interaction entities.
- Actual parsed speakers and existing identities remain valid even when their fantasy names are unusual.
- New referenced entities must resemble a specific proper individual and are rejected when they look like groups, places, events, conditions, or descriptive noun phrases.
- Strengthens the memory-summarizer instruction with explicit examples such as `children missing since the Longest Year` and `people suffering in the slums`.
- Adds **Delete Character...** to Relationships for manually removing previously-created phantom entities.
- Deleting a Relationship character does not delete Character Knowledge or Continuity facts.
- Preserves alpha5 Adaptive Characters and all earlier identity, memory, continuity, and parser behavior.
