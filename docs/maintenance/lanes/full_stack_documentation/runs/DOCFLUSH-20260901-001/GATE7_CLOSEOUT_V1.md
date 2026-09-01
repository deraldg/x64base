---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260901-COWORK-013
  recorded_at_utc: 2026-09-01T23:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: COWORK-20260826-002
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 2d26612b9
  authorization:
    requested_by: maintainer (member.derald), in-session, "start the fullstack document push next version", then "write it"
    scope: >
      Gate 7 closeout for DOCFLUSH-20260901-001 (v7). Records what the run did,
      what it got wrong, and what it hands forward. v7 mutated nothing but its
      own records; publication was never entered and is not claimed.
  report:
    path: docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260901-001/GATE7_CLOSEOUT_V1.md
    kind: gate-record
---

# DOCFLUSH-20260901-001 (v7) -- Gate 7 closeout

    run        : DOCFLUSH-20260901-001 (v7)
    lane       : full_stack_documentation
    owner      : member.derald
    steward    : member.ai.claude.cowork
    session    : COWORK-20260826-002
    branch     : development
    baseline   : 2d26612b9   (2026-09-01)
    closed at  : 0f3565fd7   (2026-09-01)
    prior      : v6 = DOCFLUSH-20260825-001. v5 = DOCFLUSH-20260812-001.
    motto      : normalize -- smooth -- improve

    STATUS     : CLOSED at Gate 7.
    PUBLICATION: NOT ENTERED, and not attempted. Phase 8 is a separate lane.

## What v7 was, in one line

A run that set out to sweep contracts and instead found that the contract
authority already existed and had been reporting its "findings" all along.

## Gates

    Gate 0    run envelope           GATE0_RUN_ENVELOPE_V1.md
    Gate 0.5  contract state         GATE0_5_CONTRACT_STATE_V1.md
    E8        mutation inventory     E8_MUTATION_INVENTORY_V1.md
    host      E2/E5/E7 package       HOST_PROOF_PACKAGE_V1.md
    forward   hints for v8           V8_HINTS_V1.md
    Gate 7    this file

Gates 1 through 6 were not run and are not claimed. v7 did not build HELP, did
not run metacollect, did not assemble a manual candidate, and did not touch the
website. E8 exists so those remain authorizable one at a time rather than by a
blanket yes.

## Entry conditions at close

    E1  dev run closed at Gate 7    THIS FILE. v7 closes.
    E2  CMDHELPCHK reflection PASS  NOT RUN. Host only; commands in the host
                                    package. No sandbox result was recorded.
    E3  contracts 100 percent       NOT MET. 1 uncovered banner
                                    (include/dottalk/scratch_sidecar.hpp), and
                                    see the coverage caveat below.
    E4  refcheck + normcheck        PASS, re-proven 2026-09-01 at 2d26612b9.
    E5  harvest after the build     N/A this run -- no build was performed, so
                                    no harvest went stale relative to one.
    E6  command-catalog.mdx         OUT OF SCOPE, carried from v6.
    E7  backup + rollback           N/A this run -- nothing was built to back up.
    E8  per-mutation authorization  ENUMERATED, which v6 did not do. Nothing
                                    requested; nothing granted; nothing done.

## What v7 actually produced

**E4 re-proven, and E3's regression caught.** v6 recorded both as PASS on
2026-08-26. Re-running them at v7's baseline found E4 still holding and **E3
regressed** -- `uncovered` had gone 0 to 1. An inherited PASS would have carried
that silently, which is the entire reason the owner ruled this run should
re-establish the entry conditions rather than start clean.

**The contract authority was found to already exist.**
`tools/fullstack_docs/stack_audit_v1.py` reports `BANNER_CENSUS`, `CONTRACT_QA`,
`DOTREF_COV`, `DEAD_REG`, `REG_POLICY` and more. v7 hand-derived three of its
outputs before running it. Its `CONTRACT_QA/MENTION_ONLY` line names the failure
mode in its own words: *"naive marker counts are inflated by these."*

**`BANNER_CENSUS/DERIVED_ONLY` retires coverage as a quality figure.** 1023 of
1079 `@dottalk.file` banners (94.8%) carry zero authored fields. The E3 target of
"100 percent" measures banner PRESENCE, not knowledge, and v7 conflated them
before the tool corrected it.

**D2 resolved, D3 done, D1 reframed.** The `layer: helper` exemption is stable at
7 and legitimate, but it and `status: implementation-helper` are disjoint
populations with zero overlap -- one concept, two spellings, handed to AIF-129.
`stack_audit_v1.py` now leads the cookbook's Phase 0.5. And D1 dissolved on the
owner's read: an orphan is only possible while dotref is STORED, so the answer is
`dotref_autogen.py`, not a new check.

**V8_HINTS written** -- the file v6 owed v7 and did not leave.

## What v7 got wrong

Five corrections, recorded rather than quietly amended, because the pattern
matters more than any one of them.

1. **"208 of 303 commands have no worked example -- the largest contract deficit
   in the tree."** Wrong. Owner: *"help has plenty of samples."* 795 EXAMPLE rows
   exist, concentrated rather than absent, and the ~26-31% figure is documented
   house knowledge -- the `.dts` corpus is the teaching surface. A recorded design
   was relabelled a defect.
2. **"20 usage contracts missing `command:`."** Wrong. 15 are
   `@dottalk.usage.voluntary` using `documents:` deliberately; 5 are prose
   mentions with no contract. Editing the 15 would have rebuilt the collision
   `convert_subcmd_to_voluntary.py` exists to remove.
3. **"v6 failed its publication entry."** Wrong, and taken from a status field
   instead of the closeout. The final stage was POSTPONED, deliberately, until
   the rest of the work is saved, staged and proven.
4. **`@dottalk.file` coverage reported as 99.9% and near-done.** Misleading; see
   `DERIVED_ONLY` above.
5. **A fabricated path.** The AIF-134 charter was written citing
   `include/dottalk/dotref.hpp` <!-- cite-check:ignore --> -- a path that has
   never existed. The file is `include/dotref.hpp`. The `cited-paths` gate caught
   it at `d206b92f8`; corrected in `0f3565fd7`.

   Recorded with the marker because this closeout QUOTES the bad path in order to
   report it, and `cite-check` cannot tell a quotation from a claim. That is the
   second time in this session the same gate has flagged a deliberate quotation --
   the first was a stale self-referential header quoted as evidence in
   `DOTTALKPP_LAUNCH_AND_DOTSCRIPT_OPTIONS_V1.md` <!-- cite-check:ignore -->,
   where two file headers name paths that do not exist. Both are the ruling shape
   OI-017 set for `cdxdemo.dts`: when the bad value IS the subject matter,
   suppress the line rather than sterilise the evidence.

**The shape common to 1, 2 and 4:** a measurement turned into a verdict before
the system was understood well enough to judge what the number meant. The shape
of 5 is different and worse -- an invented fact, caught only by a gate.

## The one habit v7 would pass on

Run the authority before forming the question. Three times this run measured,
concluded, wrote it down, and was corrected -- and each time the tree already
knew: `DEAD_REG` had the ERROR family, the house rules had the `.dts` corpus,
`CONTRACT_QA` had the inflated marker counts. `CLAUDE.md` opens by saying to walk
the portal before designing. `stack_audit_v1.py` is that walk for this lane, and
it now leads Phase 0.5 so the next run starts there.

## Owed, and to whom

    AIF-129   pick one exemption spelling -- `layer: helper` vs
              `status: implementation-helper`. Disjoint today, zero overlap.
    AIF-134   the fix ruling: FIVE dead multiword keys, router or delete.
    v8        is dotref ready to be GENERATED? That is D1's real question.
    v8        HELP backups: twelve directories, ~617 MB, nothing rotates them.
    codex     `current_fullstack_doc_push.yaml` says the run FAILED where the
              closeout says POSTPONED. One fact, two places, one wrong -- the
              north star's own signature for a missing plank. Not edited here:
              that file is `maintained_current`, stewarded by `member.ai.codex`.

## Boundary held

No HELP DATA rebuild. No metadata import. No manualgen acceptance. No website
write. No DBF, CDX or LMDB mutation. No source file changed by this run -- and
note that `src/cli/record_view.cpp` and `src/memo/x64_memo_store.cpp` are
modified in the tree by another session, which is why every v7 commit named
explicit paths and never staged `src/` or `include/`.

v7's only mutations are its own records and two owner-approved documentation
edits. That is what this lane means by driving the next span.
