# Diagram Metadata v2 Restage Candidate v1

Status: active restage candidate
Scope: full v1-to-v2 carry-forward candidate for `DIAGENTITY`, `DIAGREL`, and `DIAGART`

## Purpose

This document records the first controlled full restage of the staged diagram metadata lane from v1 headers into the v2 candidate headers.

It is intentionally conservative.

The pass does three things:

1. preserves every current v1 row
2. appends the new v2 key columns
3. fills only the join keys justified by current evidence

It does not:

- invent missing message IDs
- invent HELP `CMDKEY` values for rows that do not expose them
- invent `MEDIA_ID` / `ANCHOR_ID` values for artifacts that are not manual media records
- convert staged design rows into fake runtime proof

## Candidate files

- [DIAGENTITY_IMPORT_v2.candidate.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGENTITY_IMPORT_v2.candidate.csv)
- [DIAGREL_IMPORT_v2.candidate.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGREL_IMPORT_v2.candidate.csv)
- [DIAGART_IMPORT_v2.candidate.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGART_IMPORT_v2.candidate.csv)

## Row preservation

Current preserved row counts:

- `DIAGENTITY`: 12 -> 12
- `DIAGREL`: 12 -> 12
- `DIAGART`: 12 -> 12

No staged v1 rows were dropped.

## Mapping policy used in this pass

### `DIAGENTITY`

The pass filled explicit feeder keys only where the feeder family is already obvious from the v1 row itself.

Filled cases:

- `SRCFILE -> SRC_TABLE=SRCFILE, SRC_KEY=FILEID`
- `SRCBLOCK -> SRC_TABLE=SRCBLOCK, SRC_KEY=BLOCKID`
- `SRCLINE -> SRC_TABLE=SRCLINE, SRC_KEY=LINEID`
- `SRCUSAGE -> SRC_TABLE=SRCUSAGE, SRC_KEY=USAGEID`
- `SRCCLASS -> SRC_TABLE=SRCCLASS, SRC_KEY=CLASSID`
- `MEMO_LINES -> SRC_TABLE=MEMO_LINES, SRC_KEY=MEMOKEY`
- staged `DIAG*` tables got their natural design-only key names
- the manual draft page and gate page were mapped to `RELATIVE_P` style document keys

Left blank on purpose:

- `CAN_NAME`
- `CMDKEY`
- `MSG_ID`
- `MSG_SYMBOL`
- `MEDIA_ID`
- `ANCHOR_ID`

unless the row itself already carries enough trustworthy identity to fill them.

### `DIAGREL`

The pass preserved the current v1 relation model and lifted it into explicit physical join columns.

Filled cases:

- `FILEID` spine rows use `JOIN_TABLE=SRCFILE`, `JOIN_FIELD=FILEID`
- `COMMAND` spine row uses `JOIN_TABLE=SRCUSAGE`, `JOIN_FIELD=COMMAND`
- deferred `BLOCKID` rows use `JOIN_TABLE=SRCBLOCK`, `JOIN_FIELD=BLOCKID`
- memo simulation row uses `JOIN_TABLE=MEMO_LINES`, `JOIN_FIELD=MEMOKEY`
- staged `DIAG*` design rows use their target table plus `RUNID`

Added proof semantics:

- `REPORT_PROVEN`
- `DEFERRED_BY_DATA`
- `DESIGN_STAGING`
- `DESIGN_ONLY`

### `DIAGART`

The pass normalized every artifact path into `RELATIVE_P`.

It did not attempt to assign:

- `CMDKEY`
- `MSG_ID`
- `MSG_SYMBOL`
- `MEDIA_ID`
- `ANCHOR_ID`

because the current v1 artifact set is mainly:

- staging manifests
- gates
- ledgers
- schema pages
- import CSVs

and not actual manual-media attachment rows.

## What this candidate pass proves

This pass proves that the v2 shape is stable enough to carry the whole current staged lane without loss.

It also proves that the source-comment relation family can be normalized immediately because the v1 rows already expose:

- `FILEID`
- `COMMAND`
- `BLOCKID`
- `TEXTMEMO -> MEMOKEY`

in human-readable form.

## What is still unresolved after the candidate pass

### 1. HELP-key restaging

The full staged lane does not yet include explicit HELP artifact rows with `CMDKEY` carried on the diagram rows themselves.

Result:

- HELP joins still require a crosswalk pass, not just structural carry-forward
- the correct current boundary is documented in [DIAGRAM_METADATA_V2_HELP_ENRICHMENT_BOUNDARY_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_HELP_ENRICHMENT_BOUNDARY_v1.md)
- the proof-sample `ABOUT -> DOT|ABOUT` mapping remains valid because that packet uses a real harvested HELP artifact row, not only a structural selfdoc/design row

### 2. Metadata command restaging

The full staged lane does not yet include explicit command-identity rows such as:

- `CAN_NAME`
- `CMD_ID`

for the diagram entities outside the separate proof sample.

Result:

- the command metadata bridge is proven by sample, but not yet spread across the full staged set

### 3. Message restaging

The full staged lane has no stable message-key rows in v1.

Result:

- `MSG_ID` and `MSG_SYMBOL` remain intentionally blank in the full candidate files
- message linkage still belongs to a later crosswalk pass

### 4. Manual attachment restaging

The full staged artifact set does not yet contain real manual media artifacts.

Result:

- `MEDIA_ID` and `ANCHOR_ID` remain intentionally blank in the full candidate files
- the manual attachment bridge is proven only in the proof sample packet so far

## Correct interpretation

This candidate pass is successful, but it is not the final promotion.

It should be read as:

- structural carry-forward: yes
- source-evidence join normalization: yes
- full HELP crosswalk: not yet
- full metadata command/message crosswalk: not yet
- full manual media/anchor crosswalk: not yet

## Recommended next pass

The next pass should be a focused enrichment pass, not another structural rewrite.

Recommended order:

1. HELP enrichment pass
   fill `CMDKEY` where current diagram rows clearly correspond to HELP command/topic artifacts
2. metadata command enrichment pass
   fill `CAN_NAME` and later `CMD_ID` for command-identity rows
3. message enrichment pass
   fill `MSG_SYMBOL` and `MSG_ID` only where `SYSMSG` crosswalk evidence is strong
4. manual attachment enrichment pass
   fill `MEDIA_ID` and `ANCHOR_ID` only where real manual media artifacts are present

## Practical bottom line

The lane is now beyond design-only header work.

We have:

- doctrine
- join inventory
- v2 headers
- proof samples
- full structural restage candidates

The next work is enrichment, not reinvention.
