# Ruling State Dogfood V1 -- SYSRULING

    lane        : AIF-082
    created_utc : 2026-07-31T23:05:00Z
    updated_utc : 2026-07-31T23:05:00Z
    owner       : member.derald
    steward     : member.ai.claude.cowork
    status      : schema authored; NOT built, NOT seeded, NO runtime
    evidence    : source-evidenced. The steward cannot execute the engine.

**Precision on "syntax-checked" (owner challenge, 2026-07-31).** The ONLY check
run was `g++ -fsyntax-only -std=c++20 -Iinclude` on the C++ header. **No `.dts`
script was written for this lane, and none should be yet** -- see section 5a.
An earlier draft of this header said "authored and syntax-checked" in the status
line, which invites the reading that the seeding path was checked too. It was
not. Nothing about creating or populating the table has been executed or
verified.

## 0. Scope calibration

```text
operating_mode: feature
change_class: C2 -- adds a schema and a metadata table under the shared data root.
build_target: dottalkpp_runtime
truth_state: source-defined
proof_state: `g++ -fsyntax-only -std=c++20 -Iinclude` passes on the header. NOTHING
  else. No build, no table created, no row written, no runtime observed.
risk_class: low. A new table adjacent to existing ones; nothing reads it until it
  exists, and the console degrades to the markdown path when it does not.
minimum_gate_set: house style; syntax check; the console must still build with the
  table absent (verified).
deferred_gates_and_residual_risk: no runtime tier earned. Field widths are
  asserted from the bbs_schema conventions, not from a written and re-read row.
```

## 1. Why

The rulings console (`tools/reports/build_rulings_report.py`) can render two
kinds of dated event: a group-ratification header and a file mtime. That is all
the markdown sheet records. Two consequences, both measured 2026-07-31:

- **No history.** Individual rulings carry no dated status transition, because
  the sheet stores them as prose with an empty `Ruling` cell.
- **The hand-kept total drifts.** The sheet declared `Total open: 20`; parsing
  found **17**. A footer maintained by hand is not updated every time a row lands.

This is AIF-082's own thesis turned on the lane's governance: authored state
drifts, derived state cannot. Owner ruling 2026-07-31, verbatim: *"heck yes we
dogfood this."*

## 2. Design rule -- state in the table, prose in the sheet

`SYSRULING` deliberately does NOT carry the ruling argument. A ruling's case is
paragraphs long; `BODY` is `C(240)` (`bbs_schema.hpp:47`, "memo upgrade
deferred"), and AIF-083 F5 records that same ceiling already failing the BBS.
Storing prose here would make this table a **fourth** claimant on the 64-bit memo
work (AIF-070, AIF-082 6.10, AIF-083 F5) and block it behind a reconciliation
that has not happened.

So the split is: **sheet = argument, table = decision.** A row without a sheet
entry is an orphan and the console labels it as one; a sheet entry without a row
is simply undecided, which is the normal state and needs no row.

## 3. Schema

`include/portal/ruling_schema.hpp`, following `bbs_schema.hpp`'s `Table` /
`FieldSpec` / `N()` / `C()` pattern and reusing `namespace w` widths.

| Field | Type | Width | Meaning |
| --- | --- | ---: | --- |
| `ID` | N | 20 | monotonic row id |
| `RULEID` | C | 16 | `6.5a`, `R27b.2`, `X1` -- unique per LANE |
| `LANE` | C | 12 | `AIF-082` |
| `RULEGROUP` | C | 24 | sheet grouping, rendering only |
| `STATUS` | N | 2 | 0 proposed, 1 ratified, 2 rejected, 3 superseded, 4 withdrawn |
| `DECIDEDAT` | N | 20 | epoch seconds; 0 = undecided |
| `DECIDEDBY` | N | 20 | `SYSMEMBER` id; 0 = unknown |
| `PROPOSEDAT` | N | 20 | epoch seconds first filed |
| `STEWARD` | C | 64 | member key of the proposer |
| `SUPERBY` | C | 16 | RULEID superseding this one |
| `BLOCKS` | C | 64 | what it unblocks, e.g. `M4`, `6.6` |
| `NOTE` | C | 240 | one line: the decision, NOT the argument |
| `ROWVER` | N | 20 | row version, parallel to SYSBOARD |

**APPEND-ONLY.** A status change is a NEW row with a later `DECIDEDAT`, never an
update in place -- the same discipline as `SYSPOST`. That is what makes the table
a history rather than a snapshot. Current status of a ruling is its row with the
highest `DECIDEDAT`.

`STATUS` is ordered so numeric comparison is meaningful and an unrecognised
future value sorts last rather than silently reading as `proposed`.

## 4. What is already wired

`build_rulings_report.py` prefers `SYSRULING` and falls back to the markdown
sheets when the table is absent. Verified today in the fallback direction:
the console builds, reports `17 open, 13 ratified`, and states on the page that
the schema exists but the table is not yet seeded. It borrows `read_dbf()` out of
`build_reports.py` at run time rather than copying it, so there is one reader.

Where the table exists, it is authoritative for **status**; the sheet still
supplies proposal text, per section 2.

## 5. Maintainer handoff -- create and seed

The steward cannot build or run the engine (measured; sandbox glibc against the
binary's requirement), so everything below is host-side.

1. **Wire the schema into the store bootstrap** the same way the BBS tables are,
   and rebuild:

   ```powershell
   cmake --build build --target dottalkpp --config Release
   ```

2. **Create the table** under `dottalkpp\data\metadata\portal\`. Note the path:
   a new `portal/` sibling of `bbs/` and `identity/`, so `SYSRULING` never
   collides with an engine metadata table at the root.

3. **Seed from the sheet once**, then let the table lead. The 30 rulings parsed
   today (17 open, 13 ratified) are the natural seed; Group A's ratification
   timestamp `2026-07-31T18:22Z` is the only real `DECIDEDAT` currently recorded,
   and every other ratified row should carry it rather than a guess.

4. **Re-run the console** and confirm it switches source:

   ```powershell
   python tools\reports\build_reports.py
   ```

   The Recorded-history section should change from the "history is thin" warning
   to `Source: SYSRULING -- N append-only row(s)`.

## 5a. Why there is no seed `.dts`, and when there should be

Owner asked to see any DotScript written for a syntax check. **There is none**,
deliberately, for three reasons in increasing order of importance.

1. **Nothing can check it.** No `.dts` linter exists anywhere under `tools/`;
   only the engine parses DotScript. The steward cannot run the engine, so any
   `.dts` handed over would be **unverified by construction** -- exactly the
   evidence class this project refuses to accept as proof.

2. **The syntax has a known swallowing trap, filed by this steward today.**
   AIF-081 F5: a trailing unquoted `;` is a LINE CONTINUATION while a leading `;`
   makes a line skippable, and `is_comment_or_blank()` treats leading `;` as
   skippable while `is_comment_line()` does not list `;` at all
   (`src/cli/dotscript_lexing.cpp:84`). A marker line ending in an unquoted `;`
   silently swallows the line beneath it. Writing an unverifiable script, in a
   syntax with an open swallowing defect, against the metadata store, is a bad
   trade at any hour.

3. **A script is the wrong tool for this step.** The house pattern for creating
   default tables is C++ bootstrap that tops up idempotently on the live store:
   `kDefaultBoards` in `bbs_store.cpp` (append a row, rebuild, `BBS BOARDS`
   materialises it), and `identity_bootstrap.cpp` for permissions and roles.
   `SYSRULING` belongs on that path, not on a hand-written script.

**When a `.dts` IS the right artifact:** after the table exists, for readback
verification -- append a row, read it back, confirm field widths and the
append-only ordering hold. At that point the maintainer can run it, and it stops
being unverified. That script should be written against the real table, not
guessed at in advance.

Two capture hazards apply when that transcript is taken, both filed today and
both biasing evidence toward a FALSE NEGATIVE:

- **AIF-081:** `DOTSCRIPT ... OUT` discards the entire `cmdout` surface. Use
  `SET ALTERNATE`.
- **messaging phase22ae_6_5_10DR:** a general DOTSCRIPT shutdown exit crash is
  confirmed and isolated, fix plan held at gate `10DT`. A truncated transcript
  reads as "the command produced no output."

## 6. Open questions for the owner

1. **Does the sheet keep its hand-kept total** once the table leads, or does the
   footer come out entirely? Recommend removing it -- a second copy of a derived
   number is exactly the drift that produced the 20-vs-17 disagreement.
2. **Who writes rows?** A ruling is an owner act, so a `RULING` CLI verb under
   the owner's authority is the honest shape, not a steward-run script. That
   makes the four agency legs apply to governance itself, which is what
   `AGENCY_MODEL_V1.md` would predict.
3. **Does the BBS get a projection?** `board.governance` already projects
   `SYSGRANT` read-only (`bbs_store.cpp:262-266`). Rulings would fit the same
   shape and would put owner decisions where agents already look.

## 7. Anchor table

| Claim | Anchor |
| --- | --- |
| schema and design rule | `include/portal/ruling_schema.hpp` |
| Table/FieldSpec pattern reused | `include/bbs/bbs_schema.hpp:35-70` |
| BODY is C(240), memo deferred | `include/bbs/bbs_schema.hpp:47` |
| append-only precedent | `SYSPOST`, `src/bbs/bbs_store.cpp:298`, `:324` |
| governance projection precedent | `src/bbs/bbs_store.cpp:262-266` |
| console fallback + SYSRULING read | `tools/reports/build_rulings_report.py` |
| one reader, borrowed not copied | `read_dbf` in `tools/reports/build_reports.py:23` |
| 20-vs-17 drift | rendered by the console; sheet footer vs parse |
