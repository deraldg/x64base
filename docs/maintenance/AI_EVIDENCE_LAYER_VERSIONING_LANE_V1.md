# Evidence Layer Versioning -- The Proof Registry Was Fiction From a Clone (Lane V1)

**Status:** fixed (this pass). **Lane:** AIF-062 (continues run AIPR-20260725-001).
**Owning project:** `project.x64base.runtime`. **Evidence class:** `runtime_observed` (measured).

## The finding

`.gitignore` line 36 carried a blanket `*.log`. It was written for build and runtime noise
(`dottalk_exit_trace.log`, `dottalk_startup_trace.log`, and friends) and it does that job correctly.

It also silently swallowed **`labtalk/proofs/runs/*.log`** -- the teed transcripts that
`proofs.yaml` rows point at **as their evidence**.

Measured 2026-07-25:

| Measure | Count |
|---|---|
| Proof artifacts in `labtalk/proofs/runs/` on disk | 71 |
| Tracked by git | **0** |
| `proofs.yaml` rows citing evidence absent from a clone | **7** |
| Untracked session closeouts in `docs/maintenance/` | **57** |
| Tracked session closeouts | 18 |

So roughly **three-quarters of the completed-work record lived outside version control**, and the
proof registry's central claim -- that `runtime_observed` means a transcript exists -- was
**unverifiable by anyone who was not sitting at this machine.**

## How it surfaced (the grounded instance)

While assessing how close x64base is to an RDBMS, a partner reported that the engine had **no
write-ahead log**. The maintainer corrected it from memory, pointed at the table buffer, and the
partner found a complete, correct WAL in `src/cli/table_state.cpp`.

The partner had not been careless. It had followed the survey-first rule and read
`include/cli/table_state.hpp`, which labelled the whole section *"Persistent buffer / journal stubs"*
and the hooks *"intentionally no-op placeholders"* -- comments left over from before implementation
(AIF-061 corrected them).

But the deeper cause was this lane. The documents that would have corrected the header **existed and
were not committed**:

- `docs/maintenance/TABLE_BUFFER_WAL_DESIGN_2026-07-19.md` -- the full design, `TBJ1` format, ordering.
- `docs/maintenance/SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md` -- a proper closeout recording
  **three teed proof phases with SHA hashes**, including **Phase B: an observed crash recovery**
  (setup left an uncommitted `U 1 1 S 2:<hex "Recovered">`, the runner appended `C 1`, reopening
  replayed it, `NAME=Recovered`, log removed).
- All three `wal_phase{A,B,C}_*.log` transcripts.

A lane that was **designed, built, crash-proven, and closed out** was indistinguishable from a lane
that was never started, to anyone reading the repository.

### Second-order cost

The partner then recorded `proof.wal.dbf_record` at `state: source_defined`, reasoning that "an
untested WAL is a design, not a guarantee" and deliberately understating rather than overstating. The
caution was right in principle and **wrong in fact** -- the crash window had been tested on
2026-07-19. Invisible evidence does not merely fail to help; it actively produces **wrong records**,
and those records then propagate as the new truth.

## The fix

A targeted negation, immediately after the blanket rule, with the reasoning inline:

```gitignore
*.log
...
!labtalk/proofs/**
!labtalk/reports/**
```

Verified both directions:

- `labtalk/proofs/runs/wal_phaseA_*.log` -- **no longer ignored**.
- `dottalkpp/data/dottalk_exit_trace.log` -- **still ignored** by `*.log`.

Then committed the evidence: 81 proof/report artifacts, 57 session closeouts, and the WAL design doc.
`proof.wal.dbf_record` corrected to `runtime_observed`, citing the Phase A/B/C logs by SHA now that
they resolve in-repo.

## The principle

> **Evidence must be versioned or the proof registry is fiction.**

An evidence class (`runtime_observed`, `validated`) is a *claim about an artifact*. If the artifact
is not in the repository, the claim cannot be checked by the audience it exists for: a future
maintainer, a partner on a cold start, or a reviewer of the public record. The registry degrades into
an assertion that the author remembers something.

This is the **same failure as the `@dottalk.file` gap (AIF-050), one layer up.** There, source files
did work that no harvest could see. Here, proofs did work that no clone could see. The traceability
lane fixed the source layer; this fixes the evidence layer.

## Rule adopted (standards seed)

- **A proof row must cite an artifact that is committed.** Before setting `runtime_observed` or
  `validated`, confirm `git ls-files --error-unmatch <artifact>` succeeds. A row pointing at an
  untracked file is not evidence -- it is a note.
- **Never write a blanket ignore for an extension that evidence uses.** `*.log`, `*.txt`, and `*.csv`
  are all carriers of proof in this project. Scope ignores to *directories that generate noise*, not
  to extensions.
- **Closeouts are part of the deliverable, not a personal record.** A lane is not closed until its
  closeout and its proof transcripts are committed.

## Follow-on (not done here)

- ~~A registry validator.~~ **BUILT in this pass:** `tools/gates/validate_registries.py` checks every
  `source:`/`related:` in `proofs.yaml`, every `closeouts:` in `ai_runs.yaml`, and every written
  lesson `path:` in `lessons.yaml` -- each must resolve **and be tracked**. Lessons at `status: idea`
  are skipped (an idea legitimately has no body yet). It immediately earned itself: a manual pass had
  found 7 bad citations by checking `source:` only; the tool found **28**, including untracked lesson
  bodies, probe `.dts` files, and manualgen artifacts nobody had noticed.
  Chained with the coverage gate in `tools/gates/run_gates.py` (static; no build required).
- **`docs/datadict/specs/` (543 files)** deliberately left untracked pending a maintainer call on
  whether the DD-series is active or superseded. Not swept in blind -- that is the mistake this
  session already made once.

## Ties

- `docs/maintenance/AI_MEMO_WAL_ATOMICITY_LANE_V1.md` (AIF-061) -- the lane whose classification this
  corrects.
- `docs/maintenance/AI_RUN_TRACEABILITY_LANE_V1.md` (AIF-050) -- same failure, source layer.
- `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` -- where the rules above now live.

Owner: `member.derald`. Steward: `member.ai.claude.cowork`.
