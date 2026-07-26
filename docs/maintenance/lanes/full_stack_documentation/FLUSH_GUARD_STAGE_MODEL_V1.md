# Full-Stack Flush -- Staged Guard Model v1

Lane: full_stack_documentation
Status: proposal / review-needed
Owner: member.derald   drafted_by: member.ai.claude.cowork
Date: 2026-07-26
Supersedes: nothing. **Extends** the existing Gate 0-7 model from
`DOCFLUSH-20260722-001` -- it does not renumber or replace it.

## Why this exists

The Gate 0-7 sequence already defines *what* each stage produces. What it does
not define is *what must be true to leave a stage*. In practice that has meant
a gate can PASS on its own terms while its inputs are stale -- the 2026-07-26
session found Gate 1's catalog predating the banner backfill by 494 files, and
Gate 2/3 results computed from that stale catalog, with nothing anywhere
reporting a problem.

A flush guard is the missing piece: a **deterministic, read-only assertion run
at a stage boundary that emits dated evidence and returns a promotion verdict.**

## Core protocol

Every stage boundary obeys the same four rules.

1. **Read-only.** A guard never mutates a table, source file, or publication
   artifact. If a guard needs a candidate, the candidate is produced by the
   stage, not the guard.
2. **Deterministic.** Re-running a guard over an unchanged tree produces
   identical output except for its timestamp. Non-deterministic output cannot
   be baselined and therefore cannot gate.
3. **Evidence-emitting.** Every guard run writes a dated bundle under the run
   directory. No bundle, no promotion -- a verbal "it looked fine" is not a gate.
4. **Baseline-ratcheting.** Each guard carries a recorded baseline. Promotion
   requires that the finding count has not INCREASED. A decrease may be locked
   in deliberately; a increase blocks.

### Verdicts

| verdict | meaning | promotion |
| --- | --- | --- |
| `PASS` | no findings | proceed |
| `WARN` | known findings, count at or below baseline | proceed **only** with a named acknowledgement listing each accepted finding code |
| `FAIL` | build-breaking finding, or count regressed vs baseline | blocked |

**Acknowledgement is per-finding-code, never blanket.** "Ack all WARNs" is not
an acknowledgement; it is the absence of one.

### The ratchet rule

A baseline records what is currently wrong, not what is acceptable forever.
Rewriting a baseline to clear a regression converts the guard into decoration.
Baselines move in one direction -- down -- and each move is a deliberate act
recorded in the run log.

## Stage map

Gate numbering is inherited from `DOCFLUSH-20260722-001`. `stack_audit_v1.py`
exists today and guards the 1->2 boundary; the rest are specified, not built.

| gate | boundary | guard | state |
| ---: | --- | --- | --- |
| 0 | mission / baseline recorded | `stack_audit_v1.py --write-baseline` + run manifest | **built** |
| 1 | source contracts -> SRC* catalog | `stack_audit_v1.py` (BANNER_CENSUS, CONTRACT_QA, SRCFILE_DRIFT, EMBEDDED_BOM) | **built** |
| 2 | SRC* / metadata -> references | `stack_audit_v1.py` (CSV_VS_TABLE, DOTREF_COV) + `metacollect --compare` | **built** (audit) / **partial** (metacollect not yet baselined) |
| 3 | references -> HELP | `CMDHELPCHK` clean + HELP row-count guard vs baseline | **specified** |
| 4 | HELP -> manual / SelfDoc | manualgen test suite + page/lineage counts vs baseline | **specified** |
| 5 | manual -> website candidate | declared-vs-emitted page parity, route count, link check | **specified** |
| 6 | candidate -> commit / publish | prepush gate + scoped-slice check + deploy preflight | **partial** (prepush gate built) |
| 7 | published -> live readback | cache-bypassed fetch of every new route, artifact hash match | **specified** |

## Guard specifications

### Gate 1 -- source contracts (BUILT)

```
python tools\fullstack_docs\stack_audit_v1.py --out-dir <run>\gate1_<date>
```

Asserts: banner coverage; authored-vs-derived provenance; contract dialect
canonicality; no mention-only false positives inflating counts; no duplicate or
non-identity command names; SRCFILE catalog matches the tracked tree; no
embedded BOM anywhere in tracked source.

`EMBEDDED_BOM` is the only `FAIL`-severity finding in the audit. It is
build-breaking on MSVC and tolerated silently by GCC/clang, so it must never be
demoted to WARN and must never be verified on a Linux-only build.

Current baseline: **FAIL 0 / WARN 21**
(`stack_audit_baseline_v1.json`; verified identical on Windows and Linux).

### Gate 2 -- metadata / references (BUILT, needs metacollect baseline)

Same command; `CSV_VS_TABLE` and `DOTREF_COV` carry this boundary. Additionally:

```
metacollect.exe --source-root <src> --metadata-root <metadata> --with-metadata --compare `
                --compare-out <run>\gate2_<date>\metacollect_compare.csv
```

Asserts: no canonical lane reads a stale CSV as if it were the table; dotref
coverage is measured against the live DBF; the metacollect compare count has not
increased (frozen reference: **238** = 175 `METADATA_ONLY` + 63 `SOURCE_ONLY`).

**This is the boundary that failed silently in the past.** A coverage number is
only canonical if its input is canonical. `CSV_VS_TABLE` exists specifically to
make that failure loud.

### Gate 3 -- HELP (SPECIFIED)

Guard should assert, against a recorded baseline: `CMDHELPCHK` reports clean;
legacy command count, argument count, current topic count and line count have
not regressed; every HELP row can name its upstream source. Reference baseline
from DOCFLUSH-20260722-001: 459 legacy commands, 2,566 arguments, 575 topics,
29,197 lines.

### Gate 4 -- manual / SelfDoc (SPECIFIED)

Guard should assert: manualgen suite green (58/58 reference); command page,
lineage row, part and line counts at or above baseline; PDF builds. Reference:
191 command pages, 4,604 lineage rows, 26 parts, 14,542 lines, 298-page PDF.

### Gate 5 -- website candidate (SPECIFIED)

Guard should assert: declared pages == emitted pages (reference 117/117); static
route count at or above baseline (132); no internal link resolves 404 in the
local candidate. **Local PASS is not publication** -- Gate 5 green means
reviewable, nothing more.

### Gate 6 -- commit / publication (PARTIAL)

`tools/staging/prepush_gate.py` already hard-blocks build trees, binaries,
embedded BOM and AIF-number collisions, and warns on data fixtures and mass
change sets. Still needed: a scoped-slice assertion (per the repo's
never-`git add -A` rule) and a deploy preflight.

### Gate 7 -- live readback (SPECIFIED)

Guard should assert: every newly published route returns 200 on a
**cache-bypassed** fetch; published artifact hashes match the promoted candidate;
live manual matches the local candidate. Gates 6 and 7 are currently PENDING for
DOCFLUSH-20260722-001 -- local work is complete through Gate 5 only.

## Evidence layout

```
docs/maintenance/lanes/full_stack_documentation/
  stack_audit_baseline_v1.json                  <- Gate 1/2 baseline (ratchets down)
  runs/<RUN-ID>/
    gate<N>_<YYYYMMDD>/
      *_report.md            human-readable verdict
      *_summary.json         machine-readable, baseline-comparable
      ACKNOWLEDGEMENT.md     required iff promoting on WARN; names each code
```

Run CSVs match the `docs/maintenance/lanes/**/runs/**/*.csv` ignore rule and stay
local as evidence unless deliberately force-added. Do not weaken that rule to
make evidence committable.

## Applying this to the current run

`DOCFLUSH-20260722-001` is Gates 0-5 PASS, 6-7 PENDING. Retrofitting:

1. Gate 1/2 guards now exist and have a recorded baseline -- but the audit shows
   the **inputs to the already-passed Gates 2 and 3 were stale** (catalog predates
   the banner backfill; SYSCMD CSV 40 rows vs table 203).
2. Therefore Gates 2-4 should be **re-run after** the SRC* reload, or the
   published manual will describe a source-contract state that no longer exists.
3. Gate 6 must decide the run-CSV retention question already flagged in the
   handoff, without weakening the global ignore rule.

## Honest limits

- Only Gates 1 and 2 are enforced today. Gates 3-5 and 7 are specifications; a
  guard that is not built does not guard anything.
- The Gate 1/2 baseline currently encodes **21 WARNs as normal**. That is an
  accurate description of today, not a target. If it never ratchets down, the
  guard documents decay rather than preventing it. The four highest-value
  reductions are: refresh the stale SYSCMD CSV from the live table; reload the
  SRC* catalog; seed the three empty lanes; resolve the duplicate/non-identity
  command names.
- Guards assert structure and counts. They cannot assert that documentation is
  *correct* -- only that it is consistent with its declared sources and has not
  regressed.
