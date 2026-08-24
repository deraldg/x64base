# DEV-19 HELP/META Crosswalk and Manual Generation

```yaml
page_id: DEV-19
title: HELP/META Crosswalk and Manual Generation
status: DRAFT
last_verified: 2026-07-08
```

## Working rule

```text
Rebuild HELP from source and reference layers.
Read HELP broadly.
Read META semantically where seeded.
Validate with CMDHELPCHK.
Verify with source.
Prove with runtime.
Assemble manuals and website from the same evidence spine.
```

## Verified rebuild path

Current verified rebuild path:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Interpretation:

- `CMDHELP BUILD LEGACY` refreshes the classic `commands.dbf` / `cmd_args.dbf`
  lane when `dotref.hpp` changed
- `CMDHELP BUILD . d:\code\ccode\src` is the richer current HELP DATA pass
- `CMDHELPCHK` validates reflected structure after rebuild

The explicit source-root build harvested:

- `REGISTRY`
- `DOTREF`
- `FOXREF`
- `EDREF`
- `SHARED_MSG`
- `SOURCE_MINER`
- `USAGE_CONTRACT`

## Crosswalk purpose

The HELP/META crosswalk is not meant to replace source authority.

Its job is to:

- bind HELP topics and artifacts to semantic metadata lanes
- record what is already seeded versus what is still sparse
- keep manualgen/manual/website assembly from inventing parallel truth
- support diagrams and attached publication lanes without copying truth
  sideways

## Publication rule

Manuals and website pages should both derive upward from the same reviewed
evidence set.

Working rule:

- do not copy runtime/manual command truth back from the website
- do not let website prose become the only copy of technical truth
- when a page is not directly derived from the source project, mark it as prose
  or publication-only material

## Proposed crosswalk schema

```csv
key,kind,help_command,help_cmdkey,help_topic,help_topickey,help_status,help_implemented,help_supported,help_primary,help_confid,artifact_sources,artifact_kinds,artifact_confids,artifact_severities,meta_table,meta_id,meta_name,meta_active,meta_public,meta_dispatch_reachable,meta_handler,cmdhelpchk_status,source_file,source_owner,build_gate,proof_status,proof_id,canary_id,manual_target,derived_user_target,derived_student_target,review_status,notes
```

## Required next artifacts

```text
help-meta-crosswalk-v0.csv
help-meta-gap-report-v0.md
function-crosswalk-v0.csv
command-surface-classification-v0.md
source-miner-review-v0.md
seed-hygiene-report-v0.md
```

## Current practical next artifacts

After the verified 2026-07-07 rebuild, the most useful next pieces are:

```text
help-topic-to-manual-section-map-v1.csv
help-topic-to-website-section-map-v1.csv
shared-message-to-surface-map-v1.csv
metadata-diagram-attachment-plan-v1.md
manualgen-evidence-harvest-checklist-v1.md
```

Current concrete artifact path now added:

```text
docs/manuals/developer/manualgen/reports/manualgen-evidence-harvest-checklist-v1.md
```

Current concrete messaging/publication artifact now added:

```text
docs/manuals/developer/manualgen/reports/shared-message-to-surface-map-v1.csv
```

## Producer/toolchain crosswalk

The documentation family is not just `source -> CMDHELP -> manual`.

It includes distinct producers and validators outside the runtime shell:

- curated reference headers: `dotref.hpp`, `foxref.hpp`, `edref.hpp`
- embedded source contracts: `@dottalk.usage`
- HELP DATA harvesting and bridge code
- runtime builder/reporter: `CMDHELP`
- runtime validator: `CMDHELPCHK`
- external metadata toolchain: `dt_meta.lib` + `metacollect.exe`
- python publication lane: `tools/manualgen/manualgen.py`

Current concrete artifact path now added:

```text
docs/manuals/developer/manualgen/reports/help_meta_toolchain_crosswalk_v1.csv
```

Additional seeded family-to-section map:

```text
docs/manuals/developer/manualgen/reports/help-topic-to-manual-section-map-v1.csv
docs/manuals/developer/manualgen/reports/help-topic-to-website-section-map-v1.csv
```
