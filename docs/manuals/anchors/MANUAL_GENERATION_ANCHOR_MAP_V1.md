# Manual Generation Anchor Map v1

This directory contains machine-facing anchor material for DotTalk++ manual generation.

Primary human-readable map:

- `DOTTALKPP_MANUAL_ANCHOR_MAP_V1.md`

Primary structured map:

- `docs/manuals/anchors/manual_generation_anchor_map_v1.csv`

The anchor map joins bottom-up evidence from HELP, META, SelfDoc, cmdhelpchk, manualgen, runtime proof transcripts, source headers, and data dictionary reports to top-down reader manual sections.

Generation rule:

```text
Manual prose must consume anchored evidence.
Anchored evidence must retain source path, confidence state, and next closure action.
```
