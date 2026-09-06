# AIF-154 -- the metadata catalogue pipeline does not run

**Status:** chartered. Findings only -- NOTHING is proposed as a fix, because the
first question (is the pipeline meant to be re-runnable at all?) is unruled.
**Claim:** `coordination/aif/AIF-154.claim` (run `COWORK-20260905-002`,
`member.ai.claude.cowork`, lane `metadata-catalogue-pipeline`).
**Owner:** `member.derald`  **Author:** `member.ai.claude.cowork`
**Freshness:** 2026-09-05.

---

## 0. How this number came to exist, because it is part of the record

AIF-154 was claimed at 21:41:39Z on 2026-09-05 under lane `runtime-def-family`,
twenty-one minutes before AIF-155 (22:02:59Z) in the same run. **The claim was
made and then not used** -- the charter work went to 155 -- and the pre-push
gate flagged it: *"claim(s) with no intake row (abandoned/demo -> release-aif):
AIF-154"*.

Worse, this author then told the owner the number belonged to a co-session. The
owner corrected it (*"i think you are wrong i think aif-154 is your number?"*)
and was right. **Reading `coordination/aif/AIF-154.claim` would have settled it
in one command; asserting ownership without reading the claim file is the fourth
instance of that shape recorded on 2026-09-05.** The number is reused here rather
than released, and its `lane:` corrected from `runtime-def-family` to
`metadata-catalogue-pipeline`, because the subject is genuinely different.

## 1. The finding

`SYSFUNC.dbf`, `SYSCMD.dbf` and `SYSARGS.dbf` are **generated catalogues** --
`metacollect` builds seed rows from the live source (`all_function_docs()`, the
registry, the usage contracts) and emits import CSVs. **That pipeline cannot be
run today, and could not be loaded if it were.** Measured 2026-09-05:

| step | state |
|---|---|
| build the generator | `metacollect` is gated behind `DOTTALK_BUILD_METACOLLECT` and is **NOT** one of `build.ps1`'s targets |
| the only binary | `build/metacollect-docflush/Release/metacollect.exe`, dated **2026-07-26** -- six weeks stale, from a build directory nothing in the tree documents configuring |
| the only artifact | `SYSFUNC_IMPORT_v1.csv` at the repo root, **2026-06-27, 64 rows**, against a DBF holding 75 |
| load it back | **there is no replace-in-place path** |

**THE ARTIFACT IS STALE IN BOTH DIRECTIONS AT ONCE**, which is the detail worth
keeping: the CSV is older than the DBF (64 rows against 75), and the DBF is older
than the source (75 rows against 79 documented functions). One pipeline, two
opposite kinds of drift, and neither end is the authority.

## 2. Why the load leg is the hard one

- **`IMPORT` APPENDS.** `cmd_import.cpp:156` -- *"each data row appends a blank
  record"*. Loading a regenerated 79-row CSV over a 75-row table yields **154
  rows**, not 79.
- **`ZAP` REFUSES MEMO TABLES.** `cmd_zap.cpp:282` checks
  `A.memoKind() != MemoKind::NONE`. `SYSFUNC` carries `NOTES M`, so the
  zap-then-import idiom is unavailable *precisely on the catalogues that carry
  documentation*.
- So the obvious two-verb refresh is closed by design decisions that are each
  individually correct. Nothing is broken; the composition does not exist.

## 3. What was done instead on 2026-09-05, and why it does not generalise

`FN_COVERAGE(warn)` had named `DELETED`, `ISNULL`, `RECCOUNT` and `RECNO` since
their FunctionDocs landed. It was closed (`94782c434`) by writing a **four-row
CSV by hand** and appending it with `USE SYSFUNC` + `IMPORT` -- 75 to 79,
verified at the prompt.

**That worked because the delta was additive and tiny.** It does not scale, it
cannot express a CHANGED row, and it cannot express a REMOVED one. The moment a
function's `min_args` changes or a function is retired, hand-appending is the
wrong instrument and the pipeline is still missing.

## 4. The near miss, which is the argument for a number

`build_sysfunc_seed_rows()` set `row.calc_call = true` for **every** FunctionDoc
unconditionally. For `FunctionCategory::Cursor` that is false and this tree had
already disproved it four ways. **Had the regeneration been run before the
generator was read, it would have written that falsehood into a TRACKED
catalogue** -- and the catalogue is exactly the artifact other tools treat as
authority. Fixed in `cb6b26911` before any row was written.

A pipeline nobody can run is also a pipeline nobody audits. That is the risk this
lane names.

## 5. NOT CLAIMED

1. **That `SYSCMD` and `SYSARGS` have drifted.** They share the generator and
   therefore share the wall, but their drift was NOT measured. `SYSCMD` shows 212
   rows against a 245-command registry with 17 informational exclusions; whether
   the remainder is policy or staleness is **unmeasured**.
2. **That configuring the metacollect build is hard.** It was not attempted. The
   claim is only that no script or document in the tree does it.
3. **That regeneration is the right answer.** It may be that these catalogues are
   deliberately curated artifacts that a generator merely seeds once. Section 0's
   question is real and this charter does not answer it.
4. **Any reading of `dt_meta`'s other emitters** -- compare mode, the
   `--compare-out` report, the source-catalog facts. Unread.

## 6. Work items, unordered, none started

- **Rule first:** are these catalogues GENERATED (regenerate on demand) or
  CURATED (seeded once, hand-maintained)? Every other item depends on it.
- Make `metacollect` reachable -- a `build.ps1` switch, or a documented configure
  line for the `-DDOTTALK_BUILD_METACOLLECT=ON` build dir.
- Decide the load leg. A `REPLACE FROM` verb, an import mode that upserts on a key
  column, or a `PACK`-based rebuild that memo tables tolerate.
- Measure `SYSCMD` and `SYSARGS` drift before deciding either of the above.
- Delete or date-stamp `SYSFUNC_IMPORT_v1.csv` at the repo root -- an untracked
  Jun 27 artifact that looks current is a trap for the next reader.
