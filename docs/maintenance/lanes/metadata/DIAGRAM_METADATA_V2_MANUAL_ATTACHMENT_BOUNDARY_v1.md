# Diagram Metadata v2 Manual Attachment Boundary v1

Status: active boundary note
Scope: when `RELATIVE_P`, `MEDIA_ID`, and `ANCHOR_ID` may be promoted into diagram metadata v2 rows

## Purpose

This note records the current hard boundary for manual/publication attachment in the diagram metadata lane.

The manual lane already has real attachment identity.

But not every documentation artifact is a media attachment.

That distinction matters.

## What is proven now

### 1. The manual attachment schema is real

The manual execution schema defines:

- `MANMEDIA(MEDIA_ID, FILE_NAME, RELATIVE_P, SHA256, LENGTH_BYT)`
- `MANANCHOR(ANCHOR_ID, MEDIA_ID, MEDIA_FILE, ACTIVE_COM, ACTIVE_C01)`

Schema proof:

- [MDO_248_MAN_SCHEMA_EXECUTE_v1.dts](/D:/code/ccode/docs/manuals/developer/manualgen/generated/x64base_man_catalog_execution_v1/dts/MDO_248_MAN_SCHEMA_EXECUTE_v1.dts)

### 2. Stable media IDs and paths are already present

The current manual manifest carries real media rows with:

- `media_index`
- `file_name`
- `relative_path`
- `sha256`

Manifest proof:

- [manualgen_current_state_manifest_v1.json](/D:/code/ccode/docs/manuals/developer/manualgen/manifests/manualgen_current_state_manifest_v1.json)

### 3. Stable anchor planning is already present

The accepted media/anchor manifest assigns stable IDs such as:

- `MEDIA-STORY-001`
- `media-storyboard-cobol-connected-computers`

Accepted manifest proof:

- [MDO-219_ACCEPTED_MEDIA_ANCHOR_MANIFEST_v1.md](/D:/code/ccode/docs/manuals/developer/manualgen/accepted_manifests/MDO-219_ACCEPTED_MEDIA_ANCHOR_MANIFEST_v1.md)

That is strong enough to support proof-sample attachment rows.

## What is not the same thing as manual media attachment

Most current staged diagram artifacts are not true media rows.

They are things like:

- draft pages
- gates
- schema notes
- ledgers
- staging manifests
- import CSVs

Those artifacts can still carry:

- `PATH`
- `RELATIVE_P`

But they should not automatically carry:

- `MEDIA_ID`
- `ANCHOR_ID`

unless they are genuinely represented in the manual media/anchor lane.

## Current promotion rule

Use this rule during future enrichment:

1. If the artifact is a real manual media asset or accepted media/anchor row, it may carry `MEDIA_ID` and `ANCHOR_ID`.
2. If the artifact is a manual page, gate, schema note, ledger, or CSV input, keep it as a document artifact and do not force media identity onto it.
3. `RELATIVE_P` may be used as a bridge for both document artifacts and media artifacts.
4. Final attachment truth should prefer `MEDIA_ID` and `ANCHOR_ID` over filename-only or prose matching.

## Current lane status

Current state is:

- manual attachment schema: proven
- manifest media rows: proven
- accepted media/anchor IDs: proven
- proof-sample attachment crosswalk: proven
- full staged `DIAGART` set as true media attachment rows: not yet true

## Practical bottom line

For diagram metadata v2 today:

- `RELATIVE_P` is already valid across the wider artifact set
- `MEDIA_ID` and `ANCHOR_ID` are valid only for real manual media/anchor rows
- the full structural artifact candidate should stay conservative
- later media-enrichment passes should add true media rows rather than relabeling gates/pages/ledgers as media
