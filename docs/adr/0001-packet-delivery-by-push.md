---
status: accepted
---

# Packet delivery by push

`career-pkm` pushes each Packet to the Opening's branch in this repository, after the owner approves the Selection proposal, instead of the owner copying the file by hand. This keeps the full knowledge base out of application sessions and removes a manual relay from every application.

## Considered Options

- **Manual copy by the owner.** Safest and the previous rule, but it stalls every application session at the missing Packet and cannot be automated.
- **One session with both repositories attached.** Fast, but an application session could then read the whole knowledge base, which the application rules forbid.
- **Push of the Packet only (chosen).** The selection stays with the owner, the application session never sees unselected claims, and only the Packet crosses the boundary.

## Consequences

- Rule 8 in `career-pkm` names this push as the approved outbound path (accepted 2026-10-24, with the `/build-packet` command).
- Only the Packet is written to this repository. Commit, PR and issue text from the push carry claim IDs and paths, never resume or knowledge-base text.
- The application session reads only the Packet for career facts, as before.
