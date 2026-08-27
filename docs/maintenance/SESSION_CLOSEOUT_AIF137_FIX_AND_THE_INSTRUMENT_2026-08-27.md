---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260827-COWORK-002
  recorded_at_utc: 2026-08-27T14:10:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: null
    owner: member.derald
    committer: member.derald
  session:
    id: COWORK-20260827-001
    run_id: COWORK-20260827-001
    chat_reference: not_exposed
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: COWORK-20260826-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 21830b9a5558e7d8e05c5db6a3b753287a006217
  authorization:
    requested_by: member.derald
    scope: >
      Review the open action items one at a time. On AIF-137: option C --
      the narrow fix now, the wider resolver split as its own lane --
      with an explicit go for src/cli. Spec first, watched to fail,
      then the fix. Claim a number for the unassertable instrument.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AIF137_FIX_AND_THE_INSTRUMENT_2026-08-27.md
    kind: session_closeout
primary_topics:
  - workspace
  - multi_workspace
  - name_resolution
  - relations
  - regression_coverage
  - instrument_defect
---

# Session Closeout -- the AIF-137 fix, and the instrument that could not measure it, 2026-08-27

    Date              : 2026-08-27 (second closeout of run COWORK-20260827-001)
    Owning lifecycle  : DotTalk++ SDLC
    SDLC lane         : implementation + review
    Truth state       : RUNTIME-PROVEN for the defect and the fix, both
                        directions, on two binaries from the same tree.
                        Source-evidenced for the five uncovered reporting
                        sites and the index resolver.
    Proof state       : two interactive CLI transcripts plus a full
                        REGRESSION ALL. NOT registered: there is no proof.*
                        record.
    Mutation          : src/cli (3 files), one new .dts spec, one regression
                        registration, four documents, one intake row, one AIF
                        claim. FIRST src/ change of this run.

**SCHEMA NOTE.** `ai-report-audit-v1`, measured not chosen:
`labtalk/registries/ai_report_audit.yaml:4` pins v1 and the AIF-074 correction
records that the live validator REJECTS v2. Restated because a note nobody
repeats becomes a rediscovery.

## One-line summary

An instrument built in August that had never been read was read, fired
immediately, and the defect it found was fixed -- and reading it also proved
that the instrument itself cannot be asserted by any spec in the suite.

## Commits

    6d05e181d  AIF-137: scope every relation name resolution to the
               current workspace  (src/cli x3, spec, registration)
    <pending>  AIF-139, and the AIF-137 finding updated with its landed fix

Earlier in the same run: `cdf875387` (R129, AIF-137/138 findings, closeout,
claims, register and log rows), `98840b93e` (6.x ruled, AIF-138 raised, intake
rows), `3d79836b7` and `5d09988bd` (Codex's widowed documents and his AIF-136
implementation, committed on his behalf with a good-neighbor note).

## What was measured, in the order it happened

**THE ORDER IS THE POINT AND IS RECORDED AS SUCH.** The spec was written
BEFORE the fix and watched to fail. Had it been written after, a green would
have proved only that the code and the test agreed.

1. **The instrument fired on its first reading.** R112's ambiguity ledger was
   built 2026-08-22 and could not fire; R128 armed it 2026-08-26; on
   2026-08-27 the first reading printed
   `resolved to area 0 [REL refresh parent]` with the current handle at 3 --
   **on the second `WORKSPACE OPEN`, before any table name was typed, with
   `REL LIST` reporting an EMPTY store.** That is AIF-137.
2. **`SELECT students` crossed a workspace boundary** -- area 8 in workspace 2
   while standing in workspace 3, with workspace 3's own STUDENTS at area 21,
   and nothing said so. That made R129 sec 4's divergence runtime-proven.
3. **The spec was written and went red in both directions** -- `RPC_T1` (the
   wrong workspace's child was driven) and `RPC_T2` (the right one was not).
   Six guards green.
4. **The fix was written**, and the run's own ledger tags enumerated four call
   sites the source reading had missed. A grep after scoping those found five
   more.
5. **Both arms green**, guards unchanged, and every cross-workspace ledger line
   gone from the transcript while the in-workspace ones remained.
6. **`REGRESSION ALL` green, no `.F.` anywhere**, including `RELSCOPE2` -- the
   neighbouring spec over the same code -- and `RELJOIN`'s four-level
   `REL LIST ALL` chain.
7. **Rebuilt with the registration and re-run identical.**

## What was produced

    src/cli/workarea_util.{hpp,cpp}     find_open_area_in_workspace_ci, additive
    src/cli/set_relations.cpp           11 sites scoped
    src/cli/cmd_regression.cpp          RELWSNAME registered, array 57 -> 58
    dottalkpp/data/scripts/relation_parent_workspace_crossing.dts
    docs/maintenance/AIF139_FINDING_THE_MIGRATION_GATE_CANNOT_BE_MEASURED_V1.md
    docs/maintenance/AIF137_FINDING_RELATION_PARENT_IS_WORKSPACE_BLIND_V1.md
                                                        sec 9 added
    coordination/aif/AIF-139.claim                          allocator-written
    docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md      AIF-139 row

**PATHS IN THIS DOCUMENT ARE WRITTEN IN FULL, AND ONE WAS NOT.** The first cut
of the block above abbreviated the AIF-137 finding as
`AIF137_...WORKSPACE_BLIND_V1.md` to fit the column. The cited-paths gate
extracts repo paths from prose and reported it MISSING -- cited, not on disk --
which is a broken citation rather than an untracked file, and points at nothing
at all. Corrected in `<pending>`; recorded here rather than silently fixed,
because a shortened path inside a document whose paths are machine-read is a
mistake that reads as tidiness.

## The finding that outlasts the fix

**R112 sec 6a admits first-wins-plus-warning ONLY as an instrumented migration
phase "whose counter has to reach a measured zero" -- and nothing in the tree
can read that counter.** Three consumers of `ambiguity_count()`, none a spec.
The one spec that calls itself the tripwire runs `WORKSPACE REGISTRY` between
two markers and asserts nothing. And `cmd_workspace.cpp:4736` says the count is
"a FIELD of the registry, assertable by a spec", which is false.

**That false sentence convinced this session's author in writing before he
checked it, and he repeated it to the owner as fact.** It is recorded in
AIF-139 as the finding's own illustration: a false affirmation is worse than
silence, because a reader who checks finds the claim and stops.

**Demonstrated, not supposed:** AIF-137 fired that ledger and no spec in the
suite would have caught it. A person typing four commands did.

**Second half, runtime-proven:** the ledger fired with `ws 1 area 0, ws 1 area
2` -- both in DEFAULT -- because `CREATE` opens a second same-named table with
NO auto-rename, unlike `USE`. So `cmd_regression.cpp:465`'s claim that the
ledger is "STRUCTURALLY ZERO ... until two workspaces can be open at once" is
false and has been since before R128.

## What is scoped but NOT covered, stated rather than implied

- **Five reporting sites** -- `REL matchcount parent/child`, `REL preview
  child`, `REL enum parent/child`. They are scoped and **have no arm**,
  because every one of them produces CONSOLE TEXT and no marker in this
  language can read console text (the IDXDIFF precedent). A future edit could
  unscope any of the five and the suite would stay green. Their defect shape is
  THE COUNT DISCIPLINE: `REL LIST` standing in one workspace would print a
  match count computed from another workspace's tables -- a number that looks
  authoritative and describes the wrong rows.
- **`build_open_area_index_ci()`** -- NOT scoped and NOT fixed. `REL LIST ALL`
  does not use the singular resolver at all; it builds a whole UPPER-name map
  over every open area and hands it to a caller that looks up a chain of names.
  Scoping a MAP is a different change from scoping a LOOKUP: the map has no
  single site to filter, and its callers expect a complete picture of what is
  open. Named in the source and left for the wider split.

## What the author got wrong, recorded

1. **A classic-DBF parser read `dbf/x64`'s fixtures as eight BLANK records.**
   Those files carry version byte `0x64` -- this project's own 64-bit header --
   and the extended block was consumed as two bogus field descriptors. An empty
   result is not a measurement. Caught by checking the version byte before
   building an arm on it; the spec builds its own fixtures instead.
2. **"The count is assertable by a spec"** -- repeated from
   `cmd_workspace.cpp:4736` without checking. Retracted the same day; it is now
   AIF-139's subject.
3. **"Within one workspace no collision can form."** True of `USE`, false of
   `CREATE`. Found by running the spec's own fixture phase.
4. **The `using`-declaration would have broken the build.**
   `set_relations.cpp` imports the unscoped resolver by name; the new
   unqualified calls would not have resolved. Caught before handing over.
5. **A comment saying "TWELVE SITES" when there are ELEVEN.** A count
   discipline violation written into a comment about the count discipline, then
   counted.
6. **The spec was registered against a binary that predated the
   registration.** `REGRESSION ALL` ran without `RELWSNAME` in the list and the
   absence was invisible. Rebuilt and re-run.

## What is open

- **AIF-138** -- no fix. The `currentArea()` / `current_slot()` reader census
  is uncounted, and R129 sec 6.1a deliberately did not choose a representation
  before that count exists.
- **AIF-139** -- no fix. The external reviewer's Q4 answer reframes the target
  from "ambiguous resolutions" to "unscoped SUCCESSES down to zero", which is a
  different number and needs a ruling before anyone builds a reader.
- **The wider resolver split** -- `find_open_area_by_name_ci` into scoped /
  given-handle / explicit-cross across its 36 call sites. Option B of the C
  decision; its own lane, unclaimed.
- **The five reporting sites and the index resolver** -- above.
- **Two false comments left in place** (`cmd_workspace.cpp:4736`,
  `cmd_regression.cpp:465`), named in AIF-139 and deliberately not corrected
  inside a commit that does not otherwise touch those files.

## Verify or undo

- Verify the fix: `DO relation_parent_workspace_crossing` on any binary at
  `6d05e181d` or later. Six guards `.T.`, both arms `.T.`, no
  cross-workspace ledger lines after the two opens.
- Verify the defect: the same spec on the parent commit reads `RPC_T1 .F.`
  and `RPC_T2 .F.` with the same six guards green.
- Undo the fix: revert `6d05e181d`. The scoped resolver is additive, so
  reverting `set_relations.cpp` alone restores the old behaviour and leaves an
  unused function.
