# AIF-118 -- Silent-Pass Guard Lane: checks that cannot distinguish "absent" from "fine"

**Status:** charter (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-16. **AIF-118** (claimed 2026-08-17T01:04:55Z, run `COWORK-20260816-001`,
lane `guards-site-contrast-and-edref-shape`).
Parent project: `project.x64base.runtime` (tooling) with a publication seam.

**Sibling lanes, and this one is not first.** **AIF-100** Gate Governance owns the gate
estate; this lane owns one DEFECT SHAPE inside it. **AIF-117** *Silent Predicate and
Store Failures* is the SAME SHAPE one layer down, in the engine: `FieldRef::eval` tests
whether a field is non-blank, so `COUNT FOR <logical>` matches every row whatever its
value, an unresolvable field matches none, and `scan_selector.cpp` declares an error
string it never reads -- the engine diagnoses and the command discards. Read the two
together. AIF-117 is silence between layers of the runtime; AIF-118 is silence between
a check and its caller. Neither is a subset of the other, and a fix in one does not
touch the other.

## Why this is a lane and not five bug fixes

On 2026-08-16 five separate defects were found and closed. They looked unrelated -- a
help catalog, a git role guard, a CSS utility, a CI policy gate, a family of path
regexes. They are the same defect:

> **A check returned the same answer for "nothing is wrong" and "nothing was
> examined", and the caller could not tell the difference.**

Each had been passing for weeks or months. None had ever failed. That is the tell:
a check that has never failed has not been shown to work.

## The instances, as evidence

| # | where | what returned the same answer for absent and fine |
| --- | --- | --- |
| 1 | `refcheck_v1.catalog_names()` | `[]` for a MISSING file and `[]` for an EMPTY one, so `include/devref.hpp` sat empty for months declaring `status: supported` while `AI_TIER1_SEED_V1.md` advertised it to every agent as a working reference authority |
| 2 | `repository_role_guard.ref_is_ancestor()` | `false` for "not an ancestor" AND for "ref does not exist", so a worktree sitting on `development` read as a clean cut from `origin/main`. Found by **Codex review on PR #13**, not by the author |
| 3 | Tailwind opacity `bg-bg/78` | an off-scale value generates NO css rather than erroring, so a hero caption shipped at **1.24:1** contrast and six further utilities rendered nothing at all |
| 4 | `tools/ci/source_policy.py` | asserted a licence the project replaced on 2026-08-08, so CI failed on public main for the CORRECT repository state -- the gate WAS the drift |
| 5 | `tools/common/local_paths` predecessors | seven of nine detectors matched only `[A-Za-z]:` drive letters while agents run under WSL; 3,063 POSIX host paths were invisible to every one of them |
| 6 | `normcheck_v1.sysfunc_names()` | `set()` for a MISSING SYSFUNC and `set()` for one in perfect agreement. `FN_IDENTITY` is **fail**-severity and is computed as a set difference, so an absent authority yields zero findings -- byte-identical output to a healthy catalogue. `FN_COVERAGE` did move 0 -> 75, but it is **warn**, so a human would see seventy-five warnings and the gate would see none. FIXED 2026-08-25, proven to fail in four states |
| 7 | `refcheck_v1.function_names()` | absent, EMPTY **and unreadable** all returned `set()` -- `except Exception: return set()`. It sat forty-one lines below `catalog_state()`, this lane's own exemplary three-state repair. **The rule was applied to one reader and not to the one immediately beneath it.** FIXED 2026-08-25 |
| 8 | `refcheck_v1` precondition guard (AIF-128) | named the command registry in its message and tested the UNION of the registry with two alias sources, so it passed whenever ANY of the three resolved. **It did not fail quiet -- it failed LOUD AT THE WRONG FILE:** with the registry emptied it charged 270 correct hand-authored catalog entries and exited 1. Exit 1 says "your catalogs are wrong"; exit 2 says "I could not measure". FIXED `8c37d0ac0` |
| 9 | `build_complete_command_reference_index.py` | an `else` branch labelled anything unrecognised "supplemental" -- a layer the index describes to readers as *the accepted supplemental set*. Same answer for "known supplemental" and "never classified", **in the document whose entire job is keeping the provenance layers distinct.** FIXED `706952ef4`; every layer now DECLARED and an undeclared page FAILS |
| 10 | the page generator's own `--dry-run` | **the shape in the VERIFICATION, not the code.** The dry run returned before the write path, so it answered "fine" for a path it never executed. It passed; the real run then wrote 20 pages and died assembling its manifest. FIXED `bb6712b20` by hashing inputs before the first write |

Two more of the same shape were found in the AUTHOR'S OWN new tests, by mutation
testing rather than review: a guard test that passed with its rule deleted, and a
catalog parser that silently reported 28 of 29 because it required a trailing comma.

**Instances 6 to 10 were all found on ONE DAY, 2026-08-25**, during work that was
not looking for them -- a documentation flush. That is the lane's thesis restated
by accident: the shape is not rare and it is not clustered, it is what a guard
degrades into when nobody makes it fail.

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
`1e3a94a1d`, `df1a5e361`, `aac6b8bdf`, `ced4f4f73`, then the lane's own slice
`51af918db`, `11f94c4c8`, `29cfdbbd3`, `57de30b35`, `17e70061b`, `f809701ff`.
PR #13 merged to `main`. Site releases 126-131 published.

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

## Day two, 2026-08-17 -- the shape held, and split in half

Commits: `e9d7e3aa4`, `846b0ca02`, `a35ebe1bf`, `91e814a1d` (ccode);
`4a941f273`, `84939eeb4`, `4d35f2b3d`, `0ad92d7dc` (x64base-site).
Closeout: `SESSION_CLOSEOUT_AIF118_CONSOLE_THEME_LAB_AND_LEAN_PYDOTTALK_2026-08-17.md`.

**The lane's rule earned a corollary.** Extracting pydottalk from the monolithic
build surfaced four globals the parent had been supplying invisibly, and they
divide cleanly:

| provided silently | how it fails |
| --- | --- |
| generated `build_vectors.hpp` | compile error, immediate |
| `NOMINMAX` | compile error -- but 30+ diagnostics across 7 lines, **none naming windows.h or max** |
| `CMAKE_MSVC_RUNTIME_LIBRARY` | **links cleanly, misbehaves at runtime** |
| seven `DOTTALK_*` feature flags | **links cleanly, then corrupts** -- undefined reads as 0 under `#if`, so the module compiles a different view of the same structs than the libraries it links |

So a subproject that COMPILES is not extracted. The dangerous half of what a
parent provides produces no diagnostic at all, which is this lane's own thesis
applied to build systems rather than to checks. Recorded as
`proof.build.parent_provided_globals`.

**And the human twin of the same defect.** Four wrong conclusions this session
were each built on a CORRECT measurement -- the instrument was right and the
inference was invented: a stranger's webpage read as a lapsed domain (the
registry says it expires 2027-06-24), a collapsed nav menu read as two
disagreeing predicates, `prefers-color-scheme: dark` matched as
`color-scheme: dark`, and `git status --porcelain` without `-uall` read as a
clean directory. Two of the four reached a committed artifact before being
caught. Recorded as `proof.evidence.inference_dressed_as_measurement`, because
"measure a second way" is not enough guidance on its own: the measurement was
never the problem.

**A new rung, below the lane.** `coordination/OPEN_ITEMS.md` plus
`tools/coordination/check_open_items.py` -- small deferred work that is too
small for an AIF claim and too real to lose in chat, surfaced by the pre-push
gate only when a row's own NEXT LOOK date passes. Chosen against AIF-006's
measurement (ungated obligations 33 percent, gated 83-94) and deliberately
non-blocking, since every row is deferred by choice and a blocking gate teaches
people to delete rows.

## Still open under this lane

- **No C++ was compiled this session.** The `edref.hpp` change is additive and *should*
  compile; that is reasoning, not evidence.
- `helpdata_export_dbf.cpp:362` sets `row.title = command.empty() ? key : command`, so
  `HELP_TOPIC.TITLE` still echoes `TOPIC` for the 29 ED rows.
- Four local-path detectors deliberately not migrated -- two are rewriters, one mixes
  path detection with SECRETS, one needs a restructure. Decisions, not substitutions.
- ~~`edrefcheck_v1.py` is not wired into `prepush_gate.py`.~~ **CLOSED
  `29cfdbbd3`** -- third entry in `NORMALIZATION_GUARDS`; `include/` was already
  a trigger prefix, so it fires on an `edref.hpp` change without widening the
  trigger set. NOTE: the commit that wired it did NOT exercise it (`tools/staging/`
  is not a trigger prefix), so it was verified separately through the gate's own
  `run_normalization_guards()`, not merely by being present in the tuple.
- A `Prose.tsx` half-override guard: two light-mode readability regressions in five days,
  both from a background override without a matching foreground.
- **`refcheck_v1`'s FUNCTION half still has no precondition guard at all.**
  Currently ACCEPTABLE rather than ignored: `function_state()` three-states
  SYSFUNC, emits a finding for absent and empty, and the summary line prints
  `SYSFUNC ABSENT` instead of a number -- so the absence IS reported by name.
  But "reported somewhere" is a weaker property than "guarded", and if that
  reporting is ever simplified this becomes instance 11. (AIF-128 s8.)
- The remaining `*ref` catalogs (`pshell_ref`, `sql_ref`) were measured healthy (90 and
  33 entries) but reached through their own commands rather than the cmdhelp union.

## The lesson, stated for the next session

The defects were not found by reading code more carefully. Every one was found by
measuring a second way -- comparing a count against one taken differently, breaking a
rule on purpose to see whether a test noticed, or reading network traffic instead of
an attribute. Four of this session's own measurements were confidently wrong and were
caught the same way.

**2026-08-25 adds two variants worth naming separately.** First, the shape can
live in the VERIFICATION rather than the code (instance 10) -- a dry run that
passes because it never reaches the failing path is indistinguishable from one
that passes because the path is sound. Second, it recurs NEXT TO ITS OWN REPAIR
for the second time: instance 7 sat forty-one lines below this lane's exemplary
fix, exactly as instance 1's neighbour did.

Related: `lesson.career.a_script_never_run_is_not_evidence`,
`lesson.career.a_wrong_answer_that_looks_right`,
`proof.golden_rule_verify_before_assert`.
