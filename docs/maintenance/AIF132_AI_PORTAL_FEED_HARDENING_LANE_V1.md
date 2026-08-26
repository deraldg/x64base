# AIF-132 -- AI Portal Feed Hardening Lane V1

Status: advisory observation cycle, development tree only.

Owner: `member.derald`

Steward: `member.ai.codex`

Runs: `CODEX-20260826-001`, `CODEX-20260826-002`, `CODEX-20260826-003`,
`CODEX-20260826-004`, `CODEX-20260826-005`, `CODEX-20260826-006`,
`CODEX-20260826-007`, `CODEX-20260826-008`

## Authorization

On 2026-08-26 the owner accepted the proposed Portal hardening plan and directed
Codex to proceed. The same instruction identified concurrent Claude work in
`appgui`, multi-workplaces, and `minidb`. This lane excludes those areas.

## Objective

Create a professional typed seam from DotTalk++ documentation and data feeds to
the AI Portal without copying source databases into the Portal or confusing a
development closeout with publication.

## Scope

1. Establish `dottalk.portal.feed.v1`.
2. Register the initial HELP, metadata, manual, current-work, and Portal-report
   feeds.
3. Validate paths, hashes, lineage, evidence, retention, and visibility.
4. Prove the advisory validator with known-good and fault-injection tests.
5. Add a small recall pointer after the isolated contract/validator slice is
   green and the recall registry is rechecked for concurrent edits.

## Out of scope

- `appgui`, multi-workplaces, and `minidb`.
- HELP, metadata, manual, DBF, CDX, or LMDB mutation.
- Mutating active documentation-push state or canonical outputs. Report-only
  evidence packages may be retained under the owning run.
- `C:\x64base`, GitHub `main`, website deployment, or public publication.
- Hard-gate promotion before an advisory observation cycle and owner ruling.

## Accepted vocabulary ruling

New records use `development_closeout` and `publication_ascent`. Existing phase
numbers remain historical aliases. No historical run record is silently
renumbered.

## Milestones

| Milestone | Deliverable | Evidence gate |
| --- | --- | --- |
| M0 | Contract and lane record | PASS -- source review and ASCII check |
| M1 | Initial feed registry | PASS -- five feeds and 45 artifact observations |
| M2 | Advisory validator | PASS -- real registry returns zero findings |
| M3 | Fault-injection suite | PASS -- nine focused arms, including five named failure classes |
| M4 | Recall pointer | PASS -- recall validation and 18 recall tests green |
| M5 | Advisory integration | PASS -- scoped pre-push invocation, explicitly non-blocking |
| M6 | Current-run pointer | PASS -- typed development-closeout/publication-ascent state |
| M7 | Structured routing assertions | PASS -- six typed assertions with evidence anchors, measurement, and expiry |
| M8 | Generated status projection | PASS -- deterministic JSON and Markdown from maintained registries |
| M9 | Expanded advisory integration | PASS -- feed, assertion, and projection checks remain non-blocking |
| M10 | Professional system model | PASS -- normalized hierarchy, schema catalog, PFD, and schema crosswalk DFD |
| M11 | Full-stack entry and contract-audit hardening | PASS -- maintained run pointer plus helper-aware usage and dotref advisory |
| M12 | E5 semantic freshness gate | PASS -- report-only row-and-field comparison distinguishes current candidate from stale canonical harvest |
| M13 | Canonical harvest promotion preflight | PASS -- exact seven-row replacement plan, eight verified no-ops, hash-bound ledger, backup and rollback contract, apply disabled |
| M14 | Authorized canonical harvest apply | PASS -- seven hash-bound replacements, byte-preserved local backup, semantic E5 and manualgen readback, zero rollback findings |

## Coordination finding

The session coordinator initially assigned AIF-043 even though AIF-043 already
exists in the intake history. The claim was released immediately and AIF-132 was
claimed explicitly. This is evidence that the atomic claim-file mechanism and
the historical AIF registry are not yet one collision domain. No AIF-043 work
was modified.

## Proof plan

- Run the focused unit test module under `.venv312`.
- Run the validator against the real registry and retain its JSON observation.
- Run the Portal recall coverage and fallback-sync tests if the recall graph is
  changed.
- Check all new content for non-ASCII characters.
- Inspect exact-path Git status; do not stage or commit unrelated work.

## Execution evidence -- 2026-08-26

- `python -m unittest` over the Portal feed and recall modules: 27 tests PASS.
- Real feed validation: PASS -- five feeds, 45 artifact observations, zero
  findings.
- Recall graph validation: PASS -- no dangling edges and every node reachable.
- `recall.py fullstack_doc_push`: three-node working set -- recipe, contract,
  and current feed registry.
- Pre-push gate: PASS over exactly ten staged AIF-132 paths at the first full
  run; report audit 115/115 valid; AIF collision and claim checks PASS.
- New documentation and code checked ASCII-clean; Python modules compile.

The lane remains active only for the advisory observation cycle. Hard-gate
promotion, publication, and DBF-backed cutover each require a later owner ruling.

## Continuation evidence -- CODEX-20260826-002

The second isolated slice replaced informal current-state wording with a typed
current-run pointer and evidence-anchored assertions. Perishable assertions
carry a measurement timestamp and expiry; invariant assertions still require a
tracked evidence file and an anchor occurring exactly once. The validator uses
typed YAML value or collection checks and rejects free-text phrase matching.

The generated Portal feed status is a development-only projection. It combines
the six-feed inventory, six structured assertions, and the current documentation
push without claiming promotion, deployment, or public publication. The recall
graph routes the full-stack trigger to these maintained surfaces. Claude's
`appgui`, multi-workplaces, and `minidb` areas remain outside the slice.

## Professional model evidence -- CODEX-20260826-003

The requested architecture package is now source-backed rather than inferred
from the word `ticket`: one model defines the Project -> AIF lane -> milestone
hierarchy and keeps lifecycle, ruling, run, task, proof, and report identities
as typed related dimensions. It inventories 19 DBF table schemas registered by
Portal CRUD plus the typed registry/report schemas, and crosswalks DotTalk++
HELP, metadata, manuals, governance, evidence, Portal reports, and the website.
Two Mermaid sources preserve the PFD and DFD as reviewable text.

## Full-stack control evidence -- CODEX-20260826-004

The full-stack lane README no longer embeds an active run ID, gate state, or
dated handoff. It routes readers to the typed current-run registry and its
generated Portal projection. The current architecture recipe and the
operational command cookbook are named separately so their authority boundaries
are visible.

The source-contract audit now honors the established `@dottalk.file` field
`layer: helper`. Before the correction it reported eight command-like filenames
as missing usage contracts; seven already declared themselves helpers in their
source headers. After the correction the repository measures ten helpers, one
command file missing `@dottalk.usage`, and one declared command absent from
`dotref.hpp`. The full-stack preflight reports those separate counts as an
advisory during the observation cycle. Existing debt therefore becomes visible
without silently converting an accepted advisory into a new hard gate.

Good Neighbor note for the full-stack documentation lane:

- **WHAT CHANGED:** helper-aware contract classification, an advisory preflight
  summary, and a maintained-pointer README entry.
- **WHOSE AREA:** AIF-068 full-stack documentation controls, intersecting the
  AIF-132 Portal feed and process-model work.
- **AUTHORIZATION:** owner instruction to continue accepted hardening while
  Claude works separately on appgui, multi-workplaces, and minidb.
- **VERIFY OR UNDO:** run the two focused unit-test modules, run
  `tools/selfdoc/audit_contracts.py --strict` to observe the two remaining
  debts, and run `tools/fullstack_docs/docpush_preflight.py`; revert only the
  exact AIF-132/AIF-068 paths if the owning lane rejects the classification.

Verification: five focused audit/preflight tests pass; the 48-test full-stack
documentation suite passes; Python compilation and the integrated preflight
pass. Strict contract audit exits 1 as intended and names exactly the two
remaining advisory debts. The wider SelfDoc suite has one unrelated existing
failure: metadata-system registry entrypoint hashes no longer match ten source
files. This slice does not rewrite those hashes or claim that lane is green.

## E5 semantic freshness evidence -- CODEX-20260826-005

The Phase 8 plan now routes E5 through an executable, content-level audit rather
than a timestamp comparison. The audit reads the same 14 HELP/META DBFs as the
interim exporter, applies the same memo-cell normalization, compares every CSV
header and row, and verifies that the export manifest binds required status,
method, and current row count. It is report-only and records
`mutation_performed=0`.

Measured against the current stores, the run candidate passes 14/14 tables with
zero manifest findings. The canonical `harvested/` workspace passes 8/14 and
fails all six HELP tables; its manifest also carries six stale row counts. This
confirms E5 is open from content, not merely from file age. No canonical file or
publication pointer was changed.

Good Neighbor note for the full-stack documentation lane:

- **WHAT CHANGED:** added the E5 semantic freshness audit and corrected the
  Phase 8 plan's retired claim that no exporter exists.
- **WHOSE AREA:** AIF-068 full-stack documentation entry controls, intersecting
  AIF-132 Portal current-state routing.
- **AUTHORIZATION:** owner instruction to continue the accepted hardening plan;
  publication ascent remains separately gated.
- **VERIFY OR UNDO:** run the focused freshness tests, then run the audit once
  against the current run candidate and once against
  `docs/manuals/developer/manualgen/harvested`; revert only the four paths in
  this slice to remove the control. The audit performs no data mutation.

## Canonical harvest promotion preflight -- CODEX-20260826-006

The report-only planner converts the E5 finding into an exact selective mutation
scope. It binds all 15 candidate and canonical files by SHA-256, classifies
seven byte-changing replacements and eight byte-identical no-ops, and emits a
seven-row mutation ledger. The plan names a future byte-preserved backup root,
requires atomic replacement and complete rollback on any failure, and requires
the semantic E5 audit as post-apply readback.

Current package status is `PASS_PLAN_ONLY`: `apply_available=0`,
`mutation_authorized=0`, `canonical_files_mutated=0`, and
`publication_authority_claimed=0`. The plan manifest SHA-256 is
`82DE396E110C6361B662FDD43C7FDE677692607DC2C5B3B0EBFC17A331E42AA0`;
the mutation ledger SHA-256 is
`E5B6A3D0E0918268AF9197A694E1BDF79A00EC872940ADA8089928A2ACDF5CA2`.
The older 2026-07-18 manual authorization does not authorize this harvest plan;
a new owner authorization must bind these exact artifacts before any apply tool
or canonical write is permitted.

Good Neighbor note for the full-stack documentation lane:

- **WHAT CHANGED:** added a deterministic canonical-harvest promotion planner
  and retained its plan-only package under the current documentation run.
- **WHOSE AREA:** AIF-068 full-stack documentation E5 entry control,
  intersecting AIF-132 Portal current-state routing.
- **AUTHORIZATION:** owner instruction to begin the promotion package;
  authorization to apply the package is explicitly absent.
- **VERIFY OR UNDO:** run the focused planner tests, regenerate with the retained
  observation timestamp, and compare all three package files byte-for-byte;
  remove the planner, test, and package directory to undo this report-only
  slice. No canonical rollback is needed because no canonical bytes changed.

## Authorized canonical harvest apply -- CODEX-20260826-007/008

The maintainer's instruction to begin was transcribed into a new authorization
record bound to plan SHA-256
`82DE396E110C6361B662FDD43C7FDE677692607DC2C5B3B0EBFC17A331E42AA0`,
ledger SHA-256
`E5B6A3D0E0918268AF9197A694E1BDF79A00EC872940ADA8089928A2ACDF5CA2`,
and exactly seven mutation rows. The guarded apply/rollback implementation was
committed before execution and proved successful apply, missing-authorization
refusal, injected mid-write rollback, and manual after-hash-guarded rollback.

The authorized apply then replaced the six changed HELP CSVs and their export
manifest. Eight META/no-change files were not written. All seven before and
staged-after byte sets are retained in the repository's deliberately ignored
manualgen backup area, with hashes repeated in the tracked execution record.
The canonical CSVs are also deliberately ignored regenerable state under
`.gitignore`; durability therefore comes from the tracked producer, plan,
authorization, ledger, and execution record rather than forcing generated CSVs
into history.

Independent readback:

- canonical E5 semantic audit: PASS, 14/14 tables, zero manifest findings;
- seven target after hashes: all match the authorized ledger;
- seven backup before hashes: all match the authorized ledger;
- manualgen inventory: 14/14 harvest files;
- manualgen validation: zero FAIL, REVIEW, and boundary-fail rows;
- rollback performed: no.

The wider Phase 8 entry remains closed. Fresh measurement moved the maintained
first-open pointer to E2 because the HELP store predates the current engine. E6
also fails: the website catalog is missing APPGUI, BUILD, GUI, and SMTP, carries
two names absent from the registry, and has snapshot-count drift. Neither HELP
rebuild nor website mutation was authorized by this E5 apply.

Good Neighbor note for the full-stack documentation lane:

- **WHAT CHANGED:** authorized and applied the exact seven-row canonical harvest
  plan; added guarded apply/rollback controls and reconciled the current pointer
  to the earlier E2 blocker.
- **WHOSE AREA:** AIF-068 full-stack documentation and manualgen harvest;
  intersecting AIF-132 Portal current-state routing.
- **AUTHORIZATION:** `member.derald` instruction to begin, bound in the tracked
  authorization record to the exact plan, ledger, and row count.
- **VERIFY OR UNDO:** run the semantic E5 audit against canonical `harvested/`
  and manualgen validate. Before commit, run the tool's `rollback` command
  against the tracked execution record and local backup; after commit, revert
  the exact canonical-apply commit. No website or public rollback is required.

## SelfDoc guarded-harvest integration -- CODEX-20260826-009

SelfDoc now registers the E5 freshness, planning, authorization, apply, and
rollback chain as `META-025`. The tool and pipeline manifests describe it as a
non-default protected mutation: registration grants neither execution nor
promotion authority. A scoped validator option proves the new system's source
hash while retaining every whole-registry structural check. The ten older
entrypoint-hash drifts remain visible in the unscoped audit and were not
rewritten as incidental cleanup.

Good Neighbor note for the SelfDoc lane:

- **WHAT CHANGED:** registered the guarded HELP/META harvest control, described
  its non-default protected pipeline, and added scoped freshness validation.
- **WHOSE AREA:** SelfDoc metadata-system governance, intersecting AIF-068
  full-stack documentation and AIF-132 Portal process hardening.
- **AUTHORIZATION:** maintainer explicitly allowed this run to enter SelfDoc to
  streamline the process; no standing execution or promotion permission was
  inferred.
- **VERIFY OR UNDO:** run the focused SelfDoc unit tests and
  `validate_metadata_system_registry.py --system-id META-025 --json`; the
  unscoped validator must still report the pre-existing hash-drift debt. Revert
  only this SelfDoc integration commit to remove the registration and scope.
