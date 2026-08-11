# DotTalk++ Developer Manual

Working title: **DotTalk++ Developer Manual: Architecture, Contracts, and SelfDoc Maintenance**

Purpose: preserve architecture, invariants, source boundaries, validation discipline, and documentation-maintenance procedures.

Developer pages must show full evidence detail and identify safety boundaries.

Blocked sections include HELP/CMDHELP cookbook, CDX/LMDB indexing details, memo subsystem details, and diagram metadata implementation claims until review items are resolved.

Current command/help architecture chapters that have been materially refreshed:

- `docs/manuals/developer/dev/dev-04-architecture-overview.md`
- `docs/manuals/developer/dev/dev-05-command-system.md`
- `docs/manuals/developer/dev/dev-09-indexing-inx-cnx-cdx-lmdb.md`
- `docs/manuals/developer/dev/dev-13-browsers-and-tui.md`

These chapters now carry the open-architecture rule explicitly:

- DotTalk++ owns runtime truth
- front ends and projection layers consume that truth
- HELP, metadata, SelfDoc, manuals, and website prose describe and validate it

## Current reading order

- Coined vocabulary (global glossary, all manuals + website + AI portal):
  `labtalk/ai_portal/AI_GLOSSARY_V1.md` -- the maintained pointer index for house
  terms (walkers, name planes, learning micro/macro-systems, demonstrated
  negation, evidence tiers, ...). Definitions live in the homes it points to.
- Primary reader artifact:
  `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md`
- Current working draft bundle:
  `docs/manuals/developer/DEVELOPER_MANUAL_DRAFT_COMBINED.md`
- Publication lane index:
  `docs/manuals/developer/manualgen/published/README.md`
- Current documentation-family milestone packet:
  `docs/manuals/developer/manualgen/review_packets/MDO-381E_MANUAL_FAMILY_RUNTIME_SURFACE_ALIGNMENT_MILESTONE_PACKET.md`
- Current messaging/locale runtime alignment packet:
  `docs/manuals/developer/manualgen/review_packets/MDO-382E_MESSAGING_AND_LOCALE_RUNTIME_SURFACE_ALIGNMENT_PACKET.md`

## Lane policy

- The primary reader artifact is the stable manual a human should read first.
- Publication lanes under `manualgen/published/` may be active curation workspaces without becoming the primary reader.
- Draft bundles may be newer than the primary reader artifact without being promoted automatically.
- Reference-header catalogs are curated support layers, not the implementation layer:
  `include/dotref.hpp` and `include/foxref.hpp` are canonical live headers.
