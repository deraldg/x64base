# Manualgen Product Map v0

Status: product board companion

Open the product board:

```text
D:/code/ccode/labtalk/products/manualgen_product_board_v0.html
```

Preservation record:

```text
D:/code/ccode/labtalk/products/manualgen_product_preservation_v0.md
```

## What The Product Is

Manualgen is no longer just a script lane. It currently has these product
surfaces:

- active primary reader manual
- accepted primary reader pointer
- accepted/candidate manifests
- accepted MAN* catalog
- accepted MAN CLI docs
- MANSTAR native reference lane
- runlogs and smoke transcripts
- work-order and review-packet history

## Current Observed State

- `manualgen version`: `1.2.0-docflush`
- compatible repo-local vcpkg Python observed: `3.12.9`
- active reader file exists
- active reader observed lines: `3733`
- active reader observed H1 headings: `25` including the title
- inventory: `sections=25 media=19 appendices=12 manifests=5`
- validate with vcpkg Python 3.12.9: `validation_fail_rows=0`, `boundary_fail_rows=0`
- build dry run with vcpkg Python 3.12.9: `validation_fail_rows=0`, `dry_run_hash_matches_current_combined=0`
- explicit HELP/META harvest: `files=14/14`, `validation_review_rows=0`
- latest human reference candidate: `topics=631`, `HELP lines=12784/12784`, status `PASS`
- non-topic evidence: `global shared-message lines=2611`, `unscoped source-message facts=45`, `unclassified=0`
- command/topic resolution: `FOX compact SET aliases=8`, `unresolved=0`
- curation coverage: `topics=631/631`, `HELP lines=12784/12784`, `shelves=9`, status `PASS`
- public candidate shelves: `DOT=238`, `FOX=172`, `education=29`
- explicit topic review queue: `DOT=22`, `FOX=4`, `supplemental=23`
- review dispositions: `runtime include=20`, `partial HELP=3`, `alias merge=9`, `source appendix=6`, `developer appendix=2`, `defer=9`
- section-factory candidate: `approved topics=462`, `groups=5`, status `PASS`
- structural reconciliation: `mapped topics=462/462`, `primary=24`, `media=25`, `controlled runtime=25`, `union=26`, status `PASS`
- structural review dispositions: `13/13`, remaining review `0`, unplaced `0`
- additive section-delta candidates: `22` packets, `462/462` topic blocks, missing/duplicate/unused `0`, status `PASS`
- smallest-packet prose review: `8/8` topics, `3` candidates, additive `4`, canary cross-reference `1`, appendix-only `3`, status `PASS`
- selective merge candidate: `2` copied sections, `1` candidate appendix, `1` contextual reader, `3` diffs, section deletions `0`, canonical hash changes `0`, status `PASS`
- accepted MAN* catalog status: `GREEN`, `drift_failures=0`

## Sublanes

1. HELP / metadata harvest
2. Command reference assembly
3. Skeleton / TOC / section factory
4. Pippet section workflow
5. Publication / reader lane
6. Runtime proof lane
7. MAN* catalog lane
8. MANSTAR reference lane
9. Tooling / Python engine lane

## Product Hardening Gate

Review the full selective-merge reader and its three diffs. The generated
package preserves `GENERIC` as a canary, keeps three partial HELP topics in a
separate appendix, and changes no canonical hash. Canonical section merge,
appendix acceptance, reader rebuild, and publication remain separate gates.
The dry-run mismatch remains a classified 118-line reader overlay, and
publication/pointer changes remain separately gated.
