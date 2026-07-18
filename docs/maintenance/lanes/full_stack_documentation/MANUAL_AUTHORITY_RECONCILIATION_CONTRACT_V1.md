# Manual Authority Reconciliation Contract V1

Status: active contract; report and candidate generation only  
Established: 2026-07-16  
Authority root: `D:\code\ccode`

## Purpose

Prevent the Developer Manual's reader, assembly, historical publication, and
evidence surfaces from being collapsed into one ambiguous idea of "current."

## Named Roles

### Primary reader

The primary reader is the artifact named by:

`docs/manuals/developer/manualgen/accepted_artifacts/ACTIVE_PRIMARY_READER_ARTIFACT.txt`

This is the human reading authority. A supporting publication workspace does
not supersede it by having a newer timestamp or a name containing
`publication_v1`.

### Reader evidence record

`primary_reader_artifact_v1.json` is the evidence captured when MDO-297 created
the pointer. It is a historical evidence revision, not a continuously accurate
sidecar. If the reader content changes while the pointer target stays fixed, a
new evidence revision must be created. Do not silently rewrite the older
record.

### Accepted canonical manifest

The file named by `ACTIVE_MANUALGEN_MANIFEST.txt` is the accepted canonical
manifest revision. A manifest whose status describes an older candidate remains
historical even if it is still pointer-selected. Reconciliation requires a new
reviewed manifest revision and an explicit pointer update; it does not authorize
editing the older manifest in place.

### Assembly reference workspace

A workspace selected by manualgen for section inventory or dry-run assembly is
an assembly reference unless it is also selected by an accepted reader or
publication authority pointer. Fields and reports must say
`selected_assembly_workspace`, not imply promotion through the word `current`.

### Controlled publication target

A target replaced by an authorized historical package, such as MDO-350, remains
valid evidence for that package. Its later classification as a supporting
workspace must be recorded rather than treated as a competing primary reader.

### Overlay

Material appended outside the inventoried section list is an overlay. Every
overlay must have a named source path or manifest row, stable order, authority
classification, and Markdown validation. An assembler must not silently omit
accepted overlays or silently promote unreviewed overlays.

## Required Reconciliation Checks

Before claiming a manual is current:

1. resolve the primary reader pointer and hash its target;
2. compare the target with the latest reader evidence revision;
3. resolve the accepted canonical-manifest pointer and classify its status;
4. distinguish primary-reader, assembly-reference, controlled-publication, and
   supporting-workspace paths;
5. classify dry-run differences as section, overlay, header, order, or prose;
6. trace every content-changing reader mutation through an authorized package
   or mark the chain incomplete;
7. require a new revision for refreshed evidence; do not rewrite historical
   records merely to make hashes agree;
8. keep accepted pointers and publication replacement behind explicit gates.

## Promotion Gate

Promotion is blocked when any of the following is true:

- current reader bytes lack a complete named mutation chain;
- accepted manifest semantics describe an older candidate state;
- manualgen selects a workspace implicitly or labels an assembly reference as
  publication authority;
- overlays lack source/ordering authority or fail Markdown review;
- the proposed reader and accepted MAN* catalog do not share a reviewed run.

This contract authorizes audits, reports, and isolated candidates only. It does
not authorize reader edits, manifest acceptance, pointer changes, MAN* refresh,
publication replacement, or public projection.

Manualgen implements this role boundary through
`MANUALGEN_ASSEMBLY_WORKSPACE_SELECTION_CONTRACT_V1.md`. Evidence-bearing runs
must explicitly select the assembly workspace; legacy implicit selection is a
compatibility path and remains REVIEW.
