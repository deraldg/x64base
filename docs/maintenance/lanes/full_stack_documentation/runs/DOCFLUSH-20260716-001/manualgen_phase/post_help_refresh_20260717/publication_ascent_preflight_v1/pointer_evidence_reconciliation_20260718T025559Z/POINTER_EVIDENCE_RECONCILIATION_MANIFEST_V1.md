# Pointer evidence reconciliation manifest v1

Recorded: `2026-07-18T02:55:59Z`  
Authorization: maintainer granted  
Scope: accepted primary-reader evidence and canonical reference hash only

## Before state

| File | SHA-256 |
| --- | --- |
| `docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json` | `ADB1EEC516763F34F538B32F42F809AB3205AAD62ADA3BB537B0F9A490053A23` |
| `docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json` | `A0A8D221BB77D98DE430C8ED1B84A21A7B32AAF80A65D7422AC82B5764A8F7EA` |
| active primary reader | `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95` |

The byte-preserved before files are under `before/` in this directory.

## Authorized field reconciliation

- reader `artifact_sha256`: obsolete `777E...A8CC` to observed `0834...C95`;
- reader `artifact_lines`: `2900` to `3980`;
- reader `artifact_heading_count`: `212` to `225`;
- canonical `current_reference_sha256`: obsolete `777E...A8CC` to observed
  `0834...C95`.

## Excluded

No reader pointer, manual Markdown, section, appendix, publication workspace,
MAN* catalog, HELP/META table, source, staging repository, website, commit,
push, or deployment mutation is authorized by this reconciliation.

## Required proof

After mutation, hash the two evidence files, rerun the pointer audit, require the
four stale evidence checks to pass, and retain the intentional controlled-
publication role split as REVIEW.

## After state

Completed: `2026-07-18T02:59:29Z`  
Result: `PASS`

| File | SHA-256 after |
| --- | --- |
| `docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json` | `11071BA25F5A6C3D09B71248536A87F52A9A11AB01CF7972CA4C3370A3CCD964` |
| `docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json` | `A3EA15446766A8BDA180B76194A8D8AD852AFAEF8E021904E6E913CD1039F2E4` |
| active primary reader | `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95` |

The active reader hash is unchanged from the before state. The post-mutation
pointer audit reports 21 PASS, 1 REVIEW, and 0 FAIL. The four stale evidence
checks now pass. The one REVIEW is the pre-existing, intentional distinction
between the MDO-350E controlled-publication target and the active primary
reader.

Validation retained beneath `after_audit/`:

- full-stack documentation tests: 14 passed;
- Manualgen tests: 28 passed;
- no manual Markdown, reader pointer, or publication artifact changed.
