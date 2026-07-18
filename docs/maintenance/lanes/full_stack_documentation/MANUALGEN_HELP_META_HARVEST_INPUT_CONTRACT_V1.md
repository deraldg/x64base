# Manualgen HELP/META Harvest Input Contract v1

Status: active for evidence-bearing manualgen runs.

## Purpose

Bind a manualgen run to an exact HELP/META evidence snapshot without silently
copying that snapshot into the canonical harvest, changing accepted pointers,
or claiming publication authority.

## Required input

The caller must pass `--harvest-workspace <directory>`. The directory must
exist and contain these 14 CSV contracts:

- HELP: `HELP_CMD_ARGS`, `HELP_COMMANDS`, `HELP_HELP_ARTIFACTS`,
  `HELP_HELP_LINE`, `HELP_HELP_SECTION`, and `HELP_HELP_TOPIC`;
- META: `META_SYSARGS`, `META_SYSCMD`, `META_SYSENTVAR`, `META_SYSFLDDIC`,
  `META_SYSFUNC`, `META_SYSHELP`, `META_SYSMSG`, and `META_SYSSUBCMD`.

The selector accepts an absolute or repo-relative directory. An invalid
explicit selection fails closed. Omitting it retains the historical
`docs/manuals/developer/manualgen/harvested/` input for compatibility, but
validation returns REVIEW rather than presenting that implicit input as
current authority.

## Recorded provenance

For every required file manualgen records:

- resolved repo-relative path;
- HELP or META family;
- existence and CSV readability;
- row and column counts;
- exact header;
- SHA-256.

Inventory reports, exported state/assembly manifests, and build-dry-run
manifests carry the selected harvest and its file inventory. Generated manual
Markdown carries only the selected harvest path and selection mode as
non-content comments.

## Validation

A selected harvest passes only when all 14 files exist and have readable CSV
headers. `HELP_COMMANDS`, `HELP_HELP_LINE`, and `META_SYSCMD` must be nonempty.
Zero rows remain valid for `META_SYSARGS`, `META_SYSFUNC`, and `META_SYSMSG`;
their semantics belong to the separate metadata-contract mission and must not
be fabricated to satisfy a count.

## Authority boundary

This contract attaches evidence. `build-reference-candidate` may mechanically
project that selected snapshot into a human-view review artifact and row-level
lineage, but it does not turn generated text into an accepted manual section.
A passing assembly dry run still proves which evidence was selected, not that
every changed row appears in the existing 25 sections.

The following remain separate, explicitly authorized gates:

- replacing `docs/manuals/developer/manualgen/harvested/`;
- generating or accepting command-reference prose from harvested rows;
- moving accepted manual pointers;
- changing a published manual or external site;
- resolving the `METACOLLECT-238-20260717-001` mission.

## Current proof

The post-HELP-refresh workspace under
`DOCFLUSH-20260716-001/manualgen_phase/post_help_refresh_20260717/` passes
14/14 file checks with zero validation reviews or failures. Compared with the
May canonical harvest, seven files are unchanged and seven have compatible
content changes with unchanged headers. Total rows increase from 21,979 to
33,859. The 25 selected manual section hashes remain unchanged, proving the
existing prose assembly is not yet a harvest-driven transformation.

The reconciled mechanical reference candidate renders all 631 topics and all
12,784 HELP line rows with status `PASS`. The 2,656 blank-key lines are not
command-topic defects: 2,611 are global `SHARED_MSG` text and 45 are unscoped
`SOURCE_MINER` message-symbol facts. Both classes remain in named non-topic
appendices with zero unclassified rows.

Eight FOX compact SET command identities resolve deterministically to existing
spaced topics (`SETCASE` to `SET CASE` through `SETPATH` to `SET PATH`). The
command-resolution ledger records the original key, resolved topic key, and
`FOX_COMPACT_SET_TO_SPACED_TOPIC` rule. The source harvest remains unchanged.
