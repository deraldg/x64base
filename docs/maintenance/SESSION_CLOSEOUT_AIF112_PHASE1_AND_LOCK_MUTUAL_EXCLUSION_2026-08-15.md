---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-013
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 5f1904af6
  authorization:
    requested_by: maintainer (member.derald), in-session, "do the session close out"
    scope: >
      Session closeout. Records an AIF-112 Phase-1 exercise run host-side by the
      owner, the engine defect it uncovered, the source fix and regression that
      followed, two further lanes opened, and four governance gaps found along
      the way. Source mutation this session was owner-directed and is recorded
      under AIF-116.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AIF112_PHASE1_AND_LOCK_MUTUAL_EXCLUSION_2026-08-15.md
    kind: session_closeout
---

# Session Closeout -- AIF-112 Phase-1, and the lock defect underneath it (AIF-112)

Date: 2026-08-15.
Owning lifecycle: PDLC.
SDLC lane: proof.
Other lanes touched: **AIF-116** (opened, fixed), **AIF-113** (re-ranked),
**AIF-117** (opened), AIF-114 and AIF-031 (referenced).

## One-line summary

A Phase-1 spike built to prove a document-control ledger instead discovered that
cross-process mutual exclusion had been silently broken engine-wide on Windows
since 2025; the ledger design survived unchanged, the engine defect was
root-caused, fixed and regression-guarded the same session, and two further
lanes were opened from the wreckage.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Engine fix | `include/runtime/utf8_init.hpp`, `src/xbase/xbase_locks.cpp` | AIF-116. Locale numeric override at the cause; `imbue` on both lock writers; strict whole-field pid parse with `pid_valid`; all three stale checks fail closed. |
| Regression | `tools/regression/lock_mutual_exclusion_regression.ps1` | New. 12 assertions, 5 tests, Windows-only by design. |
| Lane docs | `LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md`, `SILENT_PREDICATE_AND_STORE_FAILURES_LANE_V1.md`, `LOCK_RELEASE_AND_RECOVERY_LANE_V1.md` | AIF-116 report; AIF-117 charter; AIF-113 re-ranked from housekeeping to blocking dependency. |
| Evidence | `AIF112_PHASE1_EVIDENCE_AND_STEWARD_HANDOFF_4_V1.md` | Filled template, all eight sections. |
| Outbound package | `external_ai_intake/aif112_phase1_return_2026-08-15/` | `AIPR-20260815-COWORK-011`; owner rulings R1-R3 drafted, unsigned. |
| Prior art | `REPORT_KIND_VOCABULARY_PRIOR_ART_V1.md` | 17 `report.kind` values surveyed; 15 have homes. |
| Spike scripts | `dottalkpp/data/dbf/sandbox/aif112_step{4,5_release,7_oracle}.dts` | Placed outside the promotion path; acknowledged as intentional fixtures. |
| Intake + claims | `AI_INTERACTION_INTAKE_QUEUE_V1.md`, `coordination/aif/AIF-11{6,7}.claim` | Two lanes claimed and registered. |
| Envelope hygiene | eight documents | `access_mode: local` -> `local_write`, session blocks added. |

Commits: `65f24d069`, `eca13fe64`, `fe42666e8`, `fcc1c2ff6`, `57c2d1634`,
`6c32f2748`, `b8dc1e6fe`, `f6233baa8`, `e5355871e`, `5f1904af6`.

## Verified (proof performed this session)

**A zero exit code is not proof.** What was actually confirmed, and how:

- **The defect, before the fix.** Two live `dottalkpp` processes, same table.
  A held `LOCK TABLE`; B read A's lock correctly (`Table: LOCKED (owner ...)`)
  and was then **granted the same lock**. Both pids confirmed alive via
  `Get-Process`. The on-disk sidecar read `pid=16,984` -- commas in the file,
  not the display.
- **The mechanism, compiled not assumed.** `std::stoul("16,984")` was built and
  run: returns `16`, does not throw.
- **The fix, re-proven.** At `fe42666e`: sidecar `77` bytes where it had been
  `87` -- the ten-byte delta is exactly the ten grouping separators. A live
  foreign owner is refused; the refused attempt leaves the holder's sidecar
  intact.
- **The recovery half, which could have been broken by the fix.** A session took
  a lock and quit while holding it; both sidecars survived process death
  (confirming from observation what source said); a fresh session reclaimed both
  and released them cleanly.
- **A suspicious number was measured, not assumed.** A reclaiming process
  reported pid `3844` replacing a dead `38444` -- same digits less one.
  `Get-Process` confirmed `3844`. Coincidence; both valid Windows pids.
- **AIF-112 Phase-1**, all eight template sections, on a live instance operated
  host-side by the owner. Step 4 run as a script twice unchanged: GRANTED then
  REFUSED, scan and append inside one FLOCK scope. `max(id)+1` observed
  allocating 3, 4, 5 across runs.
- **The regression**, 12 of 12 green -- **after** it first produced a FALSE
  failure. T5 reported a record lock granted under a foreign table lock; it had
  not been. The fixture table was empty, so `LOCK` returned "no current record".
  Fixed by verifying fixture persistence in a third process.

## AI-facing docs updated (AIF-006 gate)

- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- rows added for AIF-116
  and AIF-117; the AIF-113 row rewritten to record its re-ranking.
- `coordination/aif/` -- AIF-116 and AIF-117 claimed via `session_coordinator.py`,
  claim before row, so `check-aif-claimed` passed on both.
- `CURRENT_TARGET.md` not changed -- this session did not change the lane target;
  it executed the existing one and spawned two engine lanes beneath it.
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` -- Session Log row added.
  **Added only after the gate warned**, which makes it the fifth method note
  below. The AIF-006 warning text cites its own 33 percent compliance rate; this
  session quoted that statistic in its closeout and then supplied another
  instance of it before the commit landed.
- `content/docs/labtalk/agent-sync.mdx` (x64base-site, separate repo) -- the
  steward-facing channel: Q6 ratified, Q7 answered, Q8 settled by R2, Phase-1
  result and the three lanes recorded in the Pseudo-Chat log. **Committed on
  `codex/lean-sites-publish`, not published** -- it does not reach the steward
  until the site ships.

## Published

**Not published.** Nothing promoted to `C:\x64base` or GitHub this session.

One publication-hygiene defect was created and remediated inside the session:
spike scripts were first written to `dottalkpp/data/`, which `PROMOTE.manifest`
line 113 allow-lists for publication. Moved to `dottalkpp/data/dbf/sandbox/`,
which is not allow-listed. The tables were always outside the promotion path --
by luck, not by design, since the manifest had not been read before `CREATE`
either.

## Handoff left (AIF-082 gate, ratified 2026-07-31)

`docs/agents/HANDOFF_CLAUDE_COWORK_LOCK_SUBSYSTEM_2026-08-15.md`

Covers how to work on `xbase::locks`: the prefix-acceptance shape that caused the
defect, where each piece lives, five rules that are not obvious from the code
(fail closed; nothing releases but `UNLOCK`; Class A versus Class B; disk values
must be locale-immune; the defect is Windows-only so a green WSL suite proves
nothing), how to run the regression and how to read its failures, six traps this
session hit, and what remains broken.

No perishable facts; measuring commands given instead of counts.

## Still open -- for the next session

**Blocking:**

- **AIF-113** is now a blocking dependency, not housekeeping. `release_held`,
  `force_unlock_table`, `force_unlock_record` are dead code and no `FORCE` verb
  is exposed. Leaked Class B locks are clearable only by hand -- which this
  session hit in practice when pre-fix sidecars became unparseable and therefore
  presumed alive.

**Owner decisions, drafted and unsigned:**

- **R1** attribution (string stamp vs `N(20)` FK), **R2** ledger excluded from
  Git, **R3** `inv.break` maintainer-only -- in
  `external_ai_intake/aif112_phase1_return_2026-08-15/notes/OWNER_RULINGS_R1_R3.md`.
- Vocabulary: homes for `doctrine` and `scope`; whether to register an outbound
  `report.kind`; whether steward handoffs belong in `docs/agents/` with the rest.

**Work with a known shape:**

- **AIF-117** -- `FieldRef::eval` (`src/cli/expr/eval.cpp`) tests non-blankness;
  `scan_selector.cpp` declares an error string and never reads it. Note R3-style
  sequencing: the stricter check does not work until the error is surfaced.
- **The locale gate.** Without it, `utf8_init.hpp` is one well-meaning edit from
  re-breaking every lock. This is the durable half of AIF-116 and it is not done.
- **The audit extension**, in order: name the vocabulary, select by envelope
  rather than by glob, advisory first, then failing. Reversing that order fails
  seventeen ways on the first run and the gate gets switched off.
- **Daemon version banner.** `dottalk_bbsd` prints no build stamp, so which code
  a running daemon carries cannot be determined from its own log. Cost this
  session: four commands to establish it.
- **Transmit** Handoff 4 and the outbound package to the steward.

**Unresolved, recorded rather than guessed:**

- Why `COUNT FOR <logical-field>` returns *every* row. Three candidates
  eliminated (the predicate-chain fast path, `logical_to_num`, both `eval_bool`
  tails). `?` reads the field correctly per record while `COUNT FOR` does not --
  that divergence is the thread.

## Method notes worth keeping

Recorded because the session's own errors were as instructive as the engine's.

1. **The scribe over-claimed once and it was caught by re-reading the steward's
   template, not by the runtime.** An interim report said "all six steps passed"
   when Step 4 as specified had not been run. Written into the evidence return
   rather than quietly fixed: this lane already carries one registry entry about
   a proof process passing something on inadequate evidence.
2. **The scribe invented `access_mode: local`** by truncating `local_write`, and
   propagated it through eight commits. The registry has listed the correct value
   since its first commit; the contract publishes it as a worked example. Then
   the first investigation of that error used `git log -S'access_mode: local'`,
   which matched `local_write` **as a prefix** and wrongly exonerated the author.
   That is the same defect class as the day's root cause, committed while
   investigating it.
3. **A finished fix was dropped for an hour** because the conversation moved on
   before its commit ran. Nothing would have caught it -- the files in question
   are not audited, which is precisely what they were being fixed for.
4. **A weak oracle found a real bug.** Step 7's SQLite mirror was hand
   transcribed over an undeclared lossy mapping and the scribe said so in
   writing. It surfaced AIF-117 anyway, because the disagreement was in an
   aggregate the engine computed itself.

The common thread, and the reason AIF-117 exists: **an obligation without a gate
holds about a third of the time**, per `PREPUSH_GATE_REFERENCE_V1.md`. This
session produced four fresh instances of that in one day, from an agent that had
read the rules.

## Provenance pointers

- `docs/maintenance/LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md` (AIPR-20260815-COWORK-008)
- `docs/maintenance/AIF112_PHASE1_EVIDENCE_AND_STEWARD_HANDOFF_4_V1.md` (COWORK-009)
- `docs/maintenance/SILENT_PREDICATE_AND_STORE_FAILURES_LANE_V1.md` (COWORK-010)
- `docs/maintenance/external_ai_intake/aif112_phase1_return_2026-08-15/` (COWORK-011)
- `docs/maintenance/REPORT_KIND_VOCABULARY_PRIOR_ART_V1.md` (COWORK-012)
- `docs/maintenance/LOCK_RELEASE_AND_RECOVERY_LANE_V1.md` (COWORK-004, re-ranked)
- `docs/agents/HANDOFF_CLAUDE_COWORK_LOCK_SUBSYSTEM_2026-08-15.md`
- `tools/regression/lock_mutual_exclusion_regression.ps1`
- `labtalk/registries/proofs.d/proof.governance.availability_is_not_adoption.yaml`
- Steward packages GROK-003, GROK-004, GROK-005 -- unmodified, in
  `docs/maintenance/external_ai_intake/`.
