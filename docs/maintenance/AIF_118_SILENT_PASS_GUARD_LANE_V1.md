# AIF-118 -- Silent-Pass Guard Lane: checks that cannot distinguish "absent" from "fine"

**Status:** charter (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-16. **AIF-118** (claimed 2026-08-17T01:04:55Z, run `COWORK-20260816-001`,
lane `guards-site-contrast-and-edref-shape`).
Parent project: `project.x64base.runtime` (tooling) with a publication seam.
Sibling lane: **AIF-100** Gate Governance, which governs the gate estate. This lane
governs one DEFECT SHAPE within it.

## Why this is a lane and not five bug fixes

On 2026-08-16 five separate defects were found and closed. They looked unrelated -- a
help catalog, a git role guard, a CSS utility, a CI policy gate, a family of path
regexes. They are the same defect:

> **A check returned the same answer for "nothing is wrong" and "nothing was
> examined", and the caller could not tell the difference.**

Each had been passing for weeks or months. None had ever failed. That is the tell:
a check that has never failed has not been shown to work.

## The five instances, as evidence

| # | where | what returned the same answer for absent and fine |
| --- | --- | --- |
| 1 | `refcheck_v1.catalog_names()` | `[]` for a MISSING file and `[]` for an EMPTY one, so `include/devref.hpp` sat empty for months declaring `status: supported` while `AI_TIER1_SEED_V1.md` advertised it to every agent as a working reference authority |
| 2 | `repository_role_guard.ref_is_ancestor()` | `false` for "not an ancestor" AND for "ref does not exist", so a worktree sitting on `development` read as a clean cut from `origin/main`. Found by **Codex review on PR #13**, not by the author |
| 3 | Tailwind opacity `bg-bg/78` | an off-scale value generates NO css rather than erroring, so a hero caption shipped at **1.24:1** contrast and six further utilities rendered nothing at all |
| 4 | `tools/ci/source_policy.py` | asserted a licence the project replaced on 2026-08-08, so CI failed on public main for the CORRECT repository state -- the gate WAS the drift |
| 5 | `tools/common/local_paths` predecessors | seven of nine detectors matched only `[A-Za-z]:` drive letters while agents run under WSL; 3,063 POSIX host paths were invisible to every one of them |

Two more of the same shape were found in the AUTHOR'S OWN new tests, by mutation
testing rather than review: a guard test that passed with its rule deleted, and a
catalog parser that silently reported 28 of 29 because it required a trailing comma.

## The rule this lane exists to enforce

**A check must be able to distinguish three states, and say which it found:**
absent, empty, populated. Reporting a count is not enough -- zero findings and zero
content produce identical output.

**Corollary, and the cheaper half:** where a subject declares its own status, judge
the subject against its own declaration rather than against a hand-kept allow-list.
`refcheck_v1` now accepts an empty catalog for `status: reserved` and fails it for
`status: supported`. The list would have drifted; the declaration cannot.

## Scope

IN scope: any validator, gate, or checker in `tools/`, `scripts/` (site), or the
build chain whose failure mode is silence. Also: the guard's own tests, which must
be shown to fail before the guard is trusted.

OUT of scope: gates that already fail loudly and correctly. This lane is not a
review of the whole estate -- AIF-100 owns that.

## What landed under this lane on 2026-08-16

Commits on `development`: `199ad511b`, `dec2f3802`, `0dc63f4b9`, `b105ae99a`,
`1e3a94a1d`, `df1a5e361`, `aac6b8bdf`, `ced4f4f73`. PR #13 merged to `main`.
Site releases 126-131 published.

- `tools/common/local_paths.json` -- one authority replacing nine private regexes, with
  a 22-case test table and POSIX host coverage.
- `refcheck_v1.py` -- three-state reporting, judged against declared status. Verified by
  mutation on true exit codes.
- `edrefcheck_v1.py` -- eight arms, each proven to fire, including "empty catalog is a
  FINDING".
- `repository_role_guard.py` -- per-commit ancestry, fail-closed when development
  ancestry is unverifiable. 20 tests, three mutations.
- `check-opacity-scale.mjs` (site) -- blocks off-scale opacity in `npm run build`.
- `check-public-content.mjs` (site) -- scope narrowed to skip local-only routes, so the
  guard stops firing on content it does not govern.
- `include/devref.hpp` -- `status: supported` corrected to `reserved`.
- `include/edref.hpp` -- catalog shape settled before population; 29 one-line titles.

## Still open under this lane

- **No C++ was compiled this session.** The `edref.hpp` change is additive and *should*
  compile; that is reasoning, not evidence.
- `helpdata_export_dbf.cpp:362` sets `row.title = command.empty() ? key : command`, so
  `HELP_TOPIC.TITLE` still echoes `TOPIC` for the 29 ED rows.
- Four local-path detectors deliberately not migrated -- two are rewriters, one mixes
  path detection with SECRETS, one needs a restructure. Decisions, not substitutions.
- `edrefcheck_v1.py` is not wired into `prepush_gate.py`.
- A `Prose.tsx` half-override guard: two light-mode readability regressions in five days,
  both from a background override without a matching foreground.
- The remaining `*ref` catalogs (`pshell_ref`, `sql_ref`) were measured healthy (90 and
  33 entries) but reached through their own commands rather than the cmdhelp union.

## The lesson, stated for the next session

The defects were not found by reading code more carefully. Every one was found by
measuring a second way -- comparing a count against one taken differently, breaking a
rule on purpose to see whether a test noticed, or reading network traffic instead of
an attribute. Four of this session's own measurements were confidently wrong and were
caught the same way.

Related: `lesson.career.a_script_never_run_is_not_evidence`,
`lesson.career.a_wrong_answer_that_looks_right`,
`proof.golden_rule_verify_before_assert`.
