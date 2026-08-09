---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260809-001
  recorded_at_utc: 2026-08-09T14:30:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-fable-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 51e84f266
  authorization:
    requested_by: maintainer
    scope: >
      Owner directed clearing the CNX block on x64 files (AIF-099, run
      COWORK-20260809-001), including REBUILD/REINDEX stretch, the follow-up
      slice (Scope B verification, USE banner), the promote-final-tests rule,
      and this good-neighbor closeout. Engine proof was host-run by the owner
      and adjudicated from the datarun transcripts.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_CNX_ON_X64_2026-08-09.md
    kind: session_closeout
---

# Session Closeout -- CNX-on-x64 warn-not-refuse, proven (AIF-099)

Date: 2026-08-09. Owner/committer: member.derald. Authored by: member.ai.claude.cowork
(run `COWORK-20260809-001`; chat_handle MAINTAINER_ATTESTED). Sandbox-authored, host-proven:
every engine claim below was adjudicated from real `./datarun.ps1` transcripts, not asserted.

## What landed (commits `7011cba6a` + the follow-up slice)

CNX was a featured index before LMDB, was re-enacted to x64 standards for ramfs/vdisk in-RAM
indexing (XIDX-TXN-02 M1), but the flavor guards still refused it on x64 -- stale policy. Owner
ruling: **warn, do not refuse; CDX/LMDB stays the preferred + default x64 index.**

- `src/cli/cmd_setindex.cpp` -- explicit `.cnx` on x64 attaches with an advisory (Scope A).
- `src/cli/cmd_setorder.cpp` -- explicit container form mirrors A (C1); bare-tag fallback uses
  an existing `.cnx` when no `.cdx` exists (C2).
- `src/cli/cmd_reindex.cpp` -- bare `REINDEX` / `REINDEX ALL` route to the CNX rebuild engine
  when the ACTIVE order is CNX (fixes the observed `BUILDLMDB: failed` on a `.cnx`-ordered x64
  table). `REBUILD` itself verified guard-free -- no change needed.
- `src/cli/cmd_use.cpp` -- v64 banner now truthful: `Valid Index/Indices : CDX, CNX`.
- Scope B (`WORKSPACE OPEN DBF CNX|CDX|...`) was found ALREADY BUILT (mode parse, explicit-mode
  honor, flavor-blind attach all predate this lane); verified by regression instead of rebuilt.
- `INDEX_X64_CNX` registered (`cmd_regression.cpp`, count 34->35) + seven-phase
  `dottalkpp/data/scripts/index_x64_cnx_smoke.dts`. All seven expectations PASS on host,
  including the guard that the CDX default is UNCHANGED when no `.cnx` is requested.
  First application of the **promote-final-tests** owner rule (glossary, 2026-08-09).

## Good-neighbor notes -- cross-lane impact (owners please note)

- **Messaging/localization lane.** The three new advisories are raw `print_line` ASCII, NOT
  message-catalog entries, so they do not localize (the LANGUAGE regression does not cover
  them). Deliberate: kept the slice small. If the catalog owner wants them localized, promote
  them to MessageIds; the strings are grep-able on "advisory --".
- **HELP DATA / source-miner lane.** New comment blocks in the four cmd files will be harvested
  as SOURCE_FACTs on the next `CMDHELP BUILD`; any HELP/doc text quoting the old verbatim line
  `Valid Index/Indices   : CDX` for v64 tables is now stale and refreshes on regen.
- **Regression lane.** `kRegressionSpecs` count is now **35**; the next adder bumps to 36 (the
  in-source comment warns; I hit the papercut anyway -- the compile error is the safe failure).
- **AIF-098 (Grok / Frontal_Mem write adapter).** ZERO file overlap with this lane (bbs_schema/
  bbs_store/cmd_bbs untouched today); still apply-ready per `AIF098_BUILD_HANDOFF_V1.md`.
- **Onboarding lane (AIF-082).** Separate slices today: branch-check banner atop root
  `AI_PORTAL.md`; pointer-only replacement for main's orphaned portal drafted
  (`AI_PORTAL_MAIN_POINTER_DRAFT_V1.md`) -- awaiting owner ruling + optional peer review.
- **SANDBOX fixture owners.** Observed in the Scope B sweep: `X64SAMPLE.cdx` is a stale sidecar
  (openCdx metadata mismatch, correctly refused + explained). Pre-existing; rebuild or erase at
  leisure.
- **Glossary.** Two rules added today: one-member-id-per-deployment (owner-ratified) and
  promote-final-tests. Additive.

## Not done / follow-ups

- Advisory strings -> message catalog (messaging lane's call).
- `INDEX_X64_CNX` is explicit-run; promote to the default suite after soak.
- Older lanes unchanged: AIF-098 host apply+proof; main-pointer promotion ruling; AIF-097 Part B.
