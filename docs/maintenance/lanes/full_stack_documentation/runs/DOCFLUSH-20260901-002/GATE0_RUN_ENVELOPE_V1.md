---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260901-COWORK-014
  recorded_at_utc: 2026-09-01T23:45:00Z
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
    baseline_commit: 45f699a23
  authorization:
    requested_by: maintainer (member.derald), in-session, "leave it alone and start
      over and do it right all the way through the fullstack this time, not skipping
      steps", then "you have step by step instructions on what to do".
    scope: >
      Opens DOCFLUSH-20260901-002 (v8) and runs the cookbook in order. Report-only
      except the single @dottalk.file banner Phase 0.5 requires (recorded in the
      Gate 0.5 record). No HELP, metadata, manual, DBF, or publication mutation.
  report:
    path: docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260901-002/GATE0_RUN_ENVELOPE_V1.md
    kind: gate-record
---

# DOCFLUSH-20260901-002 -- Gate 0 run envelope

    run id     : DOCFLUSH-20260901-002        (v8)
    lane       : full_stack_documentation
    owner      : member.derald
    steward    : member.ai.claude.cowork
    run        : COWORK-20260826-002
    branch     : development
    baseline   : 45f699a23  (2026-09-01)
    opened     : 2026-09-01
    prior      : v7 = DOCFLUSH-20260901-001 (CLOSED at Gate 7, publication not
                 entered). v6 = DOCFLUSH-20260825-001. v5 = DOCFLUSH-20260812-001.
    posture    : REPORT-ONLY apart from the Phase 0.5 banner. Every mutating step
                 is enumerated and unexecuted.
    motto      : normalize -- smooth -- improve

## What v8 is, and why it is not v7 continued

v7 closed at Gate 7 having run Gate 0 and Gate 0.5 and nothing else. Gates 1
through 6 were not run and were not claimed. Its records are left untouched.

**v8 runs the cookbook in its written order, start to finish, stopping only where
the sandbox physically cannot proceed.** Where a phase needs the engine, this run
authors the artifact that phase's host command consumes and stops at that
boundary rather than skipping past it.

Read first, before any work, per `V6_HINTS_V1.md` section 8:
`FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md`, `..._COOKBOOK_V1.md`,
`DOCFLUSH-20260812-001/V6_HINTS_V1.md`, and v7's `V8_HINTS_V1.md`.

## Phase ledger

    Phase 0    run envelope                    THIS FILE
    Phase 0.5  contract coverage               GATE0_5_CONTRACT_STATE_V1.md   CLEARED
    Phase 1    inventory and classify drift    GATE1_REFERENCE_DISPOSITION_V1.md  DONE
    Phase 2    pre-refresh runtime baseline    runtime_baseline/  AUTHORED, NOT CAPTURED
    Phase 3    reviewed HELP refresh package   help_refresh/      GENERATED
    Phase 4    execute HELP refresh            OWNER-RUN ON THE HOST. PASS.
    Phase 5    metadata candidates             candidates produced, nothing imported
    Phase 6    manual candidate                candidate only, boundary_fail_rows=0
    Phase 7    review and close                next
    Phase 8    publication ascent              NOT ENTERED. Separate lane.

    Gates 4, 5, 6 and E5: GATE4_5_6_REFRESH_AND_CANDIDATES_V1.md

`docpush_preflight` exited 2 on `help_build_order_check` when this envelope was
opened and **now PASSES**: the owner ran Phase 4 on the host, LEGACY first, and
the store's half-run state is closed. Phase 0.5 had already cleared on its own
gate before that; the ordering FAIL was always Phase 4's to fix.

**Phase 2 was authored and never captured.** The `.dts` is in place and correct,
but the owner ran the Phase 4 build directly, so no pre-refresh transcript exists
and the Phase 4 before/after comparison cannot be made for this run. That is a
recorded gap, not a silent one: the counts are known from the build output
(473 -> 666 topics) but the targeted-topic arm -- the 26 changed contracts and the
five dead multiword keys -- was never read against the OLD store, so this run
cannot say which of them were stale and which were already current. The script
stands for v9, or for a re-run before the next refresh.

## Entry conditions, measured at THIS baseline

Not inherited. v7's own finding was that an inherited PASS carries a regression
silently -- E3 read PASS on 2026-08-26 and had regressed by 2026-09-01.

| E | condition | v8 state, measured 2026-09-01 at 45f699a23 |
| --- | --- | --- |
| E1 | dev run closed at Gate 7 | open; this run |
| E2 | CMDHELPCHK reflection PASS | **HOST ONLY. Not run, not claimed.** |
| E3 | contracts 100 percent | **PASS.** census 1080/1080, uncovered=0, coverage 100.0% |
| E4 | refcheck + normcheck | **PASS**, both arms re-run today |
| E5 | harvest re-exported AFTER the build | blocked: no build has been performed |
| E6 | command-catalog.mdx regenerated | **HOLD** -- site branch question unruled |
| E7 | backup + rollback named | package generated, backup not taken (Phase 4) |
| E8 | per-mutation authorization | enumerated; nothing requested, nothing done |

## The Phase 4 boundary, stated once

`docpush_preflight.py` FAILs `help_build_order_check` and will keep failing until
the HELP store is rebuilt on the host:

    store  2026-08-26 05:09:48   predates exe 2026-09-01 11:22:29
    LEGACY 2026-08-28 20:55:43   is 63h45m NEWER than the store

That is a half-run: LEGACY was rebuilt and the current store was not. The fix is
Phase 4 and it is the maintainer's, requiring the engine, an elevated
`Get-Process dottalk_bbsd | Stop-Process -Force`, and a fresh backup first.

**Every HELP-derived number in this run is therefore measured against a stale
store and is labelled as such wherever it appears.** v7 did not label them.

## Boundary for this run

NOT authorized by this envelope: HELP DATA rebuild, metadata import, manualgen
acceptance, website publication, or any DBF/CDX/LMDB write. The one source edit
this run makes is the `@dottalk.file` banner the cookbook's Phase 0.5 requires,
and it is named in the Gate 0.5 record.

No commit from this run stages `src/` or `include/` as a directory. Paths are
named individually: the tree carries other sessions' in-flight work.
