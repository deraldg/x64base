# Handoff -- PLDC to PDLC vocabulary merge (no lane)

    from        : member.ai.claude.cowork, 2026-08-07
    for         : AIF-092, and any session that paused while this pass ran
    doctrine    : docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md
    posture     : merge committed and closed. Safe to resume. Three renames moved
                  under you; nothing else in your working set was touched.

This records **how to work around what moved**, not what happened. Verify every
claim below rather than trusting it -- the pass that produced it under-reported
its own scope once already (section 4).

---

## 0. Resume check, in order

1. `git --no-optional-locks status --short` -- your uncommitted work is intact.
   This pass staged per-path slices only and never ran `git add -A`.
2. Re-point any reference you hold to the three renamed paths (section 1).
3. If you cite the doctrine's lifecycle vocabulary, re-read it. Two lifecycles
   became one (section 2).
4. If you have run a tree-wide search today and drawn a conclusion from the
   count, re-run it with `--no-ignore` before you trust it (section 4).

## 1. What moved -- three renames, history preserved

    docs/maintenance/SQLSEL_PLDC_LANE_V1.md          -> SQLSEL_PDLC_LANE_V1.md
    docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md -> X64BASE_AGENT_SKILL_PDLC_LANE_V1.md
    docs/planning/SDLC_PLDC_PLANNING_ADOPTION_v0.md  -> SDLC_PDLC_PLANNING_ADOPTION_v0.md

Git detected all three as renames, so `git log --follow` still works. Every
in-tree referrer was repointed in the same commit; measure with a grep for the
old names rather than assuming.

A fourth file was renamed but was never tracked, so git sees a new file, not a
rename: `PUBLICATION_SURFACE_RECOVERY_PLDC_LANE_V1.md` ->
`PUBLICATION_SURFACE_RECOVERY_PDLC_LANE_V1.md`. **It is still untracked.** If it
is yours, it is waiting for you.

## 2. What the merge decided, so you do not relitigate it

PLDC ("Product/Lab Delivery Cycle") is retired and folded into PDLC. What changed
is PDLC's **scope**, which now spans both the change and the deliverable. What
did NOT change is its **name**: PDLC remains the **Programming** Development Life
Cycle.

That distinction was decided the hard way. An intermediate revision of this merge
renamed it "Project" and was reverted the same day, because
`PDLC_STUDENT_WORKING_MODEL_LANE_V1.md:27` teaches PDLC-at-the-desk against
SDLC-at-the-org, and "Programming" is load-bearing in that contrast. Commit
messages from `c0d3069c5` and `018bd0c9f` still say "Project Development Life
Cycle" and are wrong on that point; the doctrine file is authoritative, not the
commit subject.

This **reverses** ruling R1 in the agent-skill lane, which had ruled that PLDC
was canonical and PDLC the typo. R1 is struck through in place and superseded by
R8, dated 2026-08-07, in the same ledger. The strikethrough is deliberate -- do
not tidy it away; it is the only readable record that the reversal happened.

Doctrine of record is the "Lifecycle vocabulary" section, which now also names
the mode switch the two-term split used to give for free: PDLC nests inside an
SDLC **when the unit is a change**, and packages reviewed SDLC and LabTalk truth
**when the unit is a deliverable**. That wording came from AIF-092's review, not
from this session.

## 3. Deliberate PLDC survivors -- leave them

A grep for `PLDC` will not return zero, and that is correct:

- The struck-through R1 and the superseding R8 in the agent-skill lane.
- The dated merge note under the doctrine's vocabulary table.
- 23 files under `docs/manuals/developer/manualgen/backups/**`. Dated escrow
  snapshots. Rewriting a preservation record to match current vocabulary
  falsifies it. Measure the count yourself; an earlier report said ten.

Widening a search does not license widening an edit. Classify before editing:
documents get corrected, escrow gets left, generated artifacts get regenerated
from source rather than hand-patched.

## 4. The failure mode this pass hit -- do not inherit it

Every sweep here used ripgrep, which **honors `.gitignore` by default**. Two
entries hid live misses, including a bundle packaged for an outside model. The
session reported "zero PLDC remains" repeatedly, with counts, and every one of
those reports was scoped to a subset without saying so.

The edit and the verification shared a tool, so the verification could only
confirm that the region it could see was clean. Confidence rose each pass while
coverage never moved. An independently-scoped session found the miss in minutes.

Confirm the mechanism in your own tree with `git check-ignore -v <path>`, and by
comparing `rg --no-ignore <term>` against `rg <term>`. Full write-up:
`labtalk/lessons/career/a_gitignored_path_is_invisible_to_your_sweep_v0.md`.

## 5. Left unfinished, deliberately -- these may be yours

- **Five tracked files hold uncommitted PDLC edits** behind other sessions'
  work: `PROMOTION_PROCESS.md`, `AI_SYSTEMS_CROSSWALK_V1.md`,
  `AI_SYSTEMS_INTEGRATION_SDLC_CHARTER_V1.md`, and two session closeouts. Staging
  them would have fused ~570 foreign lines into a vocabulary commit. When you
  land your work in those files, the PDLC edit rides along -- check the diff.
- **`portal_truth_audit_latest.{md,json}` are hand-edited, not regenerated.**
  `labtalk/portal/labtalk_portal.py` imports tkinter at module scope, so the
  headless `--audit-write` path cannot run under the repo venv, whose base
  interpreter has no `_tkinter`. Pre-existing defect, unrelated to the merge, not
  fixed here because the file is not this session's to change. The GUI Audit
  button calls the same writer if you need the artifact today.
- **`docs/ai-friendly/gptbase_bundle_v1/` is hand-corrected and gitignored.** Its
  provenance markers show it is assembled from site and repo sources. The text
  now matches its upstream byte-for-byte, so a regeneration is a no-op -- but a
  regeneration is still what it wants.
- **The lesson in section 4 is filed as a lesson, not a gate.** Its `next_gate`
  asks whether sweep-scope belongs in `prepush_gate.py` instead. AIF-082 measured
  unenforced obligations at 33 percent against 83-94 for gated ones, so a lesson
  is likely the weaker instrument -- but that is a change to someone else's tool
  and was left as a question rather than decided.

## 6. What this session did not touch

`tools/staging/prepush_gate.py`, the AIF-090 lane, `next-env.d.ts`,
`app/portal/[...slug]/`, `content/portal/`, `scripts/normalize-eol.ps1`, and
every `src/`, `tests/`, and `include/` path. No source file was edited. No
`.cpp`, `.hpp`, `.h`, or `.py` in the tree ever contained `PLDC`; the correctly
spelled `PDLC` in `test_pdlc_foundation_smoke.cpp`, the CMake comments, and the
`// lane: triggers-pdlc` headers is untouched and byte-identical.
