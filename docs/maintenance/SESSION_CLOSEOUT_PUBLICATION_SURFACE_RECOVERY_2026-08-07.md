---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260807-002
  recorded_at_utc: 2026-08-07T16:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: daa266e0d
  authorization:
    requested_by: maintainer
    scope: >
      Owner directed recovery of orphaned public documents, ruled that
      MANIFEST.txt be derived rather than authored, asked whether the AIF
      allocator was baked into the workflow, and on the measured answer said
      "harden it".
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PUBLICATION_SURFACE_RECOVERY_2026-08-07.md
    kind: session_closeout
---

# Session Closeout -- publication surface recovery and allocator hardening (AIF-092)

Date: 2026-08-07.
Owning lifecycle: PLDC.
SDLC lane: implementation.
Truth state: source-evidenced (docs and tooling; no engine behavior touched).
Proof state: fixtures + git-verified.

## One-line summary

Gave six public-facing documents a source of truth on D:, replaced a wrong
hand-written manifest with a derived publication receipt, and closed the front
half of the AIF anti-collision loop -- which had an allocator nobody was
required to use.

## Changed (development, D:\code\ccode)

| Area | File | Commit |
| --- | --- | --- |
| Public docs | `CONTRIBUTING.md` (new D: source + branch guidance) | `c686f0219` |
| Public docs | `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `RELEASE_NOTES.md` | with the above |
| Tooling | `tools/staging/generate_public_manifest.py`, `MANIFEST.txt` | `d083e6ea4` |
| Lane | `docs/maintenance/PUBLICATION_SURFACE_RECOVERY_PLDC_LANE_V1.md` | `daa266e0d` |
| Coordination | `tools/coordination/check_aif_claimed.py` | `daa266e0d` |
| Gate | `tools/staging/prepush_gate.py` (check 6, advisory) | `daa266e0d` |
| Registry | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-092 row) | `daa266e0d` |
| Claim | `coordination/aif/AIF-092.claim` | `daa266e0d` |

Pushed through `d083e6ea4..daa266e0d`.

## Verified (proof performed this session)

**The derived manifest, measured not asserted.** 80 allow-list patterns, 828
files, 0 empty; SYSCMD 212, SYSFUNC 74, SYSARGS 249, SYSHELP 8, SYSENTVAR 12,
SYSFLDDIC 16 -- read live through `tools/fullstack_docs/dbfread.py`. Fixtures:
report / write / check-after-write / doctored-content-must-fail (exit 2) /
regenerate-restores-pass. ASCII clean, tool and output.

**The allocator gate, proven both directions.** A synthetic added row naming an
unclaimed number returns 2; `--warn` returns 0 on identical input; a prose
mention of an AIF number is not mistaken for a table row. True positive
confirmed against `e9d2033d3~1..e9d2033d3` -- the commit that really did add the
AIF-090 row -- where it detected and named it.

**And the gate's first live run validated its own registration:**
`check-aif-claimed: PASS -- new row(s) AIF-092 cite claimed numbers`, in the
maintainer's pre-commit output on `daa266e0d`.

**Not verified:** no engine build, no runtime execution, no DotScript. Nothing
in this lane may claim runtime evidence.

## Four defects produced and caught in one session

Recorded because they are all the same shape -- a thing that reports success
without doing its job -- and all four were produced while building tools whose
purpose is to prevent exactly that.

1. **Silent-fallback zero.** A DBF probe used `hasattr(t, "records")` with an
   `else []`, printing `rows=0` for a 53 KB table with 212 rows. The attribute
   is `rows`.
2. **A generated artifact that was not a fixed point of its own generator.**
   Writing the allow-listed receipt changed the file count it reports, so
   `--check` failed immediately after `--write`.
3. **A phantom defect rate, nearly published.** `Path.glob("a/**")` yields
   directories, not files, so the tool was about to report 29 of 80 allow-list
   patterns broken. Corrected figure: 0.
4. **A false pass in a fixture.** The first allocator-gate positive test printed
   "no new intake rows in scope" and was nearly logged green -- the row was
   unstaged, so `diff --cached` had seen nothing.

Three of the four were caught only by distrusting a clean result. That is the
transferable lesson, not the individual bugs.

## AI-facing docs updated (AIF-006 gate)

Lane charter (sections 4, 6, 6a), intake row AIF-092, dashboard Session Log row,
this closeout. `CURRENT_TARGET.md` deliberately unchanged -- AIF-092 is not the
declared controlling target.

## Published

Committed and pushed to `origin/development`. **Not promoted to `C:\x64base`.
Not published.** Nothing an outside contributor reads has changed; the recovered
documents reach `main` only when a staging rebuild carries them, and that is
maintainer-operated.

## Handoff left (AIF-082 gate)

No new handoff file. `docs/agents/HANDOFF_CLAUDE_COWORK_AGENT_SKILL_2026-08-06.md`
covers the working posture, and this lane's own charter carries its open list.
A second handoff repeating either would be the divergence AIF-082 exists to
prevent.

## Still open -- for the next session

1. **Two gates await their flip.** `check_seed_budget.py` and
   `check_aif_claimed.py` both run `--warn` as pre-push checks 5 and 6. After a
   clean cycle, drop `--warn` and treat `rc == 2` as blocking. Until then, each
   gate's own lesson applies to itself.
2. **`WORKFLOW_X64BASE.md`** -- orphaned on `main`, contradicts `AI_PORTAL.md`
   on the same branch. Retire or source: owner's call.
3. **`MANIFEST.txt text eol=lf`** in `.gitattributes`. The generator writes LF,
   `.txt` is `text=auto`, so git stores CRLF and the file shows perpetually
   modified. `CMakeLists.txt` already uses this remedy.
4. **Wire `generate_public_manifest.py --check`** into the pre-push gate, and
   **regenerate the receipt at promotion time** so its provenance names the
   commit actually being published.
5. **AIF-091** holds a claim with no intake row. It is a live concurrent
   session, not abandonment -- do NOT release it. The advisory persists until
   that session registers, and a standing advisory is one people learn to
   ignore.
6. **65 pre-coordination intake rows** have no claim file. The new gate
   grandfathers them by checking added rows only; they drain at whatever pace
   the owner chooses, or never.

## The finding worth keeping

`PROMOTION_PROCESS.md:112` already named the GONE condition and already
prescribed the remedy -- "pull them back into development so they are not
orphaned". The doctrine was correct and unexecuted for months, while six
documents on the public branch quietly became unmaintainable.

The same shape appeared in the allocator: `claim-aif` was correct, atomic, and
optional. Correct doctrine and correct tooling are not the same thing as an
enforced workflow, and the gap between them is invisible until something
measures it.

## Provenance pointers

- Lane: `docs/maintenance/PUBLICATION_SURFACE_RECOVERY_PLDC_LANE_V1.md`
- Origin finding: `docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md`
  and `docs/maintenance/external_ai_intake/aif090_cold_probes_2026-08-06/`
- Doctrine executed: `PROMOTION_PROCESS.md` sections 6 and 8
