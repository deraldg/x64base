# Manual canonical acceptance preflight v1

Run: `DOCFLUSH-20260716-001`  
Candidate: `MANRUN-20260718T020658Z-BFE7F605`  
Status: `PASS_POINTER_EVIDENCE_RECONCILED`  
Mutation performed: four accepted evidence fields only

## Target resolution

The selective merge used the correct active primary reader:

`docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md`

Observed SHA-256:
`08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95`.

The 25-section `developer_manual_publication_v1_media_section_v1` workspace is
an explicit supporting assembly reference with publication authority `0`. The
MDO-350E controlled publication target is another retained publication role.
Neither silently replaces the active primary-reader pointer.

## Initial pointer audit

Fresh report-only audit result: 17 PASS, 5 REVIEW, 0 FAIL.

| Review | Disposition |
| --- | --- |
| Primary-reader recorded hash is `777E...A8CC`, observed is `0834...C95` | Repair required before accepted mutation. |
| Primary-reader record says 2,900 lines, observed is 3,980 | Repair required before accepted mutation. |
| Primary-reader record says 212 headings, observed is 225 | Repair required before accepted mutation. |
| Canonical manifest records the same stale `777E...A8CC` reference hash | Repair required before accepted mutation. |
| MDO-350E controlled publication target differs from primary reader | Intentional role split; retain as REVIEW unless authority is explicitly changed. |

The first four reviews mean the accepted evidence describes an earlier reader
revision. They are not content failures, but they prevent a fail-closed
canonical acceptance because the recorded before-state is stale.

## Reconciliation result

The maintainer authorized the exact four-field accepted-evidence repair. The
operation preserved byte-for-byte before copies and changed only:

- primary-reader `artifact_sha256`, `artifact_lines`, and
  `artifact_heading_count`;
- canonical manifest `current_reference_sha256`.

The active reader remained unchanged at
`08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95`.
The fresh pointer audit now reports 21 PASS, 1 REVIEW, and 0 FAIL. The retained
REVIEW is the intentional MDO-350E/primary-reader role split. Gate 2 is green.

## Controlled acceptance scope after reconciliation

An authorized acceptance operation would:

1. verify the active reader and both target-section hashes against a newly
   reconciled accepted evidence record;
2. create a timestamped, hash-verified backup of the active reader, both target
   sections, appendix aggregate/manifest surfaces, primary-reader evidence, and
   canonical manifest;
3. replace only the two accepted section copies;
4. add `partial_help_reference.md` as an explicitly accepted partial appendix;
5. rebuild the primary reader from accepted sections and appendices without the
   candidate-only header;
6. regenerate accepted hashes, line/heading counts, appendix inventory, and
   reader evidence;
7. rerun manualgen validation, pointer audit, and contextual diff checks;
8. retain a rollback manifest and before/after hashes.

## Protected surfaces

Only the four authorized accepted-evidence fields changed. No primary reader,
reader pointer, section, appendix, MAN* catalog, HELP/META table, source file,
website, commit, push, or publication surface changed during this preflight.

## Next gate

Use `MANUALGEN_CONTROLLED_ACCEPTANCE_PLAN_V1.md` to review the fail-closed
canonical section/appendix acceptance operation. The plan may be prepared and
tested without touching the manual, but its eventual apply mode remains a
separate protected mutation requiring explicit authorization.
