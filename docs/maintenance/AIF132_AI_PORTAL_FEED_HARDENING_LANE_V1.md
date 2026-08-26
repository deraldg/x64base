# AIF-132 -- AI Portal Feed Hardening Lane V1

Status: advisory observation cycle, development tree only.

Owner: `member.derald`

Steward: `member.ai.codex`

Run: `CODEX-20260826-001`

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
- Editing the active documentation-push run.
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
