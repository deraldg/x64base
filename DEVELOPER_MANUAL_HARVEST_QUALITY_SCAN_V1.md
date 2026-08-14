# Manual Harvest Inspection Quality Scan v1

Status: INSPECTION_ONLY. This is a generated reading/triage artifact, not a promoted publication.

Generated: 2026-06-28 from local repository files in `D:/code/ccode`.

## Inventory Totals

- Included source files: 27
- Total bytes: 256469
- Total lines: 6260
- Markdown headings: 436
- Manifest: `manual_harvest_inspection_manifest_v1.csv`

## Manualgen Catalog Health Observed

- `manual catalog status` reported `status=DRIFT`, `tables_readback=16`, `drift_failures=8`.
- The expected MAN* tables themselves read back with passing counts: MANRUN 3, MANSECTION 25, MANMEDIA 9, MANANCHOR 9, MANHASH 13, MANREVIEW 3, MANPUB 4, MANAPPX 6.
- The eight failures are duplicate `EXTRA_MAN_DBF` rows for those same accepted DBFs. Treat this as a manualgen/catalog visibility issue until the drift reader is repaired, not as proof that the published prose is unusable.

## Marker Counts

| Marker family | Count |
|---|---:|
| todo_tbd_fixme | 1 |
| draft_candidate | 257 |
| placeholder_stub | 23 |
| needs_review_hidden | 51 |
| canary_proof | 211 |
| drift_fail_unknown | 29 |
| raw_catalog_markers | 0 |

## Human Consumption Triage

Green: the DotTalk++ handoff, DotScript/x64/schema/index instructions, and the LabTalk case framing are readable enough for a human developer or an AI handoff reader. They explain workflow, command idioms, evidence expectations, and schema rules rather than only listing raw artifacts.

Yellow: the main developer manual publication has substantial useful command and architecture coverage, but it still carries internal publication language, generated catalog language, review/deferred appendices, and manualgen process artifacts. It is good inspection material and a strong source pool, but should be curated before being advertised as a polished user manual.

Red: anything that depends on the MAN* catalog status should not be treated as clean until the duplicate `EXTRA_MAN_DBF` drift condition is fixed or explicitly waived. Case documents that are proof-backed are useful; any hidden/review-gated cases should stay out of a public-facing manual until reviewed.

## Recommended Next Manual Shape

1. Keep the generated inspection bundle as source evidence, not the public manual.
2. Promote a smaller reader-facing manual from the strongest sections: overview, build/run, DotScript, `DO X64`, schema creation, DBF/index workflow, browsing/search/navigation, and LabTalk cases.
3. Move MAN* catalog internals, mutation cycle notes, review/deferred material, and raw proof logs into appendices for maintainers.
4. Fix or document the MAN* duplicate drift behavior before using `manual catalog status` as a release gate.

## Review Examples

| Marker | Source | Line | Text |
|---|---|---:|---|
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 155 | - MDO-189 Draft Fill |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 202 | Draft notes: |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 204 | - Generated command pages are draft evidence, not final command reference prose. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 212 | - Command reference hygiene packages must not delete generated command pages during manual draft assembly. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 258 | But generated pages can also expose draft artifacts. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 261 | - Generated command pages are draft evidence. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 264 | - They should not be deleted or rewritten during ordinary manual draft assembly. |
| placeholder_stub | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 277 | - an internal owner or command-family scaffold; |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 332 | - Slug collisions should not be resolved by deleting generated pages during manual draft assembly. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 345 | - a canonicalization candidate. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 381 | - SET-family generated pages should be treated as draft evidence. |
| placeholder_stub | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 392 | - AGGS appearing in generated command pages may indicate internal owner exposure, scaffold leakage, or family grouping evidence. |
| drift_fail_unknown | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 435 | - generated HELP drift; |
| drift_fail_unknown | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 454 | - SYSMSG for parser, syntax, unknown command, invalid argument, and ambiguity diagnostics. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 475 | - Crosswalks may be candidate, partial, or verified. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 501 | - Draft generated pages are review material. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 507 | Command-reference hygiene must preserve generated evidence during manual draft assembly. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 523 | - Review must not delete generated pages during manual draft assembly. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 530 | - generated pages draft evidence not final reference |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 545 | This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check: |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 548 | - generated pages are framed as draft evidence, not final reference; |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 591 | - prose draft fill only |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 593 | - no reviewed candidate generated |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 612 | - MDO-167 Draft Fill |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 655 | Draft notes: |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 657 | - Generated command draft pages remain draft evidence, not final command reference prose. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 674 | This draft uses several evidence lanes. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 725 | The command-surface section must not let generated command pages or metadata rows become stronger proof than they are. A generated command page is draft evidence. A metadata row... |
| placeholder_stub | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 823 | - AGGS appearing as executable or printing usage may be scaffold/debug leakage unless explicitly accepted. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 824 | - Generated command pages for AGGS are draft evidence, not final public-surface proof. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 834 | - SET-family pages may exist as generated draft evidence. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 852 | - Generated pages identify draft evidence. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 854 | - Command reference generation must not delete or rewrite generated command pages during manual draft assembly. |
| drift_fail_unknown | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 863 | - CMDHELPCHK can detect gaps and drift. |
| drift_fail_unknown | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 879 | - SYSMSG for parser diagnostics, unknown command messages, syntax errors, invalid arguments, and ambiguity warnings. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 881 | - HELP_COMMANDS and generated command pages as draft evidence lanes that require dedupe, alias, and slug-collision review. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 904 | This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check: |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 907 | - generated command pages are treated as draft evidence; |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 912 | - generated command pages with duplicates, aliases, and slug collisions remain draft evidence; |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 948 | - prose draft fill only |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 950 | - no reviewed candidate generated |
| needs_review_hidden | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 963 | Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 966 | Skeleton section generated from the revised manual TOC draft. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 969 | - This section is a structural draft. |
| needs_review_hidden | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 999 | Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1002 | Skeleton section generated from the revised manual TOC draft. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1005 | - This section is a structural draft. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1036 | - MDO-152 Draft Fill |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1076 | Draft notes: |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1078 | - Generated command draft pages remain draft evidence, not final command prose. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1094 | This draft uses several evidence lanes. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1121 | - Generated command pages may identify draft command evidence. |
| placeholder_stub | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1226 | - AGGS being executable or printing usage may be debug/scaffold leakage unless explicitly accepted. |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1227 | - Generated command pages for AGGS are draft evidence, not final public-surface proof. |
| drift_fail_unknown | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1294 | - unknown field or expression; |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1308 | - generated command draft pages; |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1325 | - generated command pages draft evidence |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1347 | This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check: |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1350 | - generated command pages are treated as draft evidence; |
| draft_candidate | `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md` | 1387 | - prose draft fill only |

