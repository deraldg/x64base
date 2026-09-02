# DOCFLUSH-20260901-002 -- E5's gate is inverted

    run       : DOCFLUSH-20260901-002 (v8)
    baseline  : 45f699a23
    owner     : member.derald
    steward   : member.ai.claude.cowork
    measured  : 2026-09-02, against export run HELPMETA-20260902T012620Z
    posture   : REPORT-ONLY. No tool changed. No harvest promoted.

## The finding in one line

**`check_help_meta_harvest_freshness.py` passes the memo-BLANK harvest and fails
the memo-BEARING one.** E5 certifies the interim Python scaffold and rejects the
engine.

## How it was found

The owner ran the sanctioned producer,
`dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1`, which exports
through `datarun.ps1` with `EXPORT ... CSV`. Result:

    E5 FAIL: 5/14 tables match; manifest_findings=14

Nine tables CONTENT_MISMATCH -- **with row counts that match EXACTLY**:

    HELP_COMMANDS        source 462    harvest 462    first_mismatch=2
    HELP_CMD_ARGS        source 2368   harvest 2368   first_mismatch=2
    HELP_HELP_ARTIFACTS  source 14844  harvest 14844  first_mismatch=2
    HELP_HELP_LINE       source 29700  harvest 29700  first_mismatch=2
    HELP_HELP_SECTION    source 14844  harvest 14844  first_mismatch=2
    HELP_HELP_TOPIC      source 666    harvest 666    first_mismatch=2
    META_SYSARGS         source 249    harvest 249    first_mismatch=2
    META_SYSFUNC         source 75     harvest 75     first_mismatch=2
    META_SYSSUBCMD       source 31     harvest 31     first_mismatch=2

Identical counts, and every table diverging at the FIRST DATA ROW, is not
staleness. It is a rendering difference. Measured:

    HELP_COMMANDS.csv, 462 rows both ways

      ENGINE  (datarun EXPORT CSV)   USAGE 462/462 non-blank
                                     VERBOSE 462/462 non-blank
      PYTHON  (dbfread scaffold)     USAGE 0/462
                                     VERBOSE 0/462

**The mismatch IS the memo text arriving.**

## Why the gate inverts -- three bindings to the scaffold

`tools/fullstack_docs/check_help_meta_harvest_freshness.py`:

    line 23-24   import dbfread
                 from export_help_meta_harvest import HELP_TABLES, META_TABLES, _cell
    line 128     table = dbfread.read(dbf_path)

The checker builds its SOURCE rendering with the same `dbfread` the scaffold
uses. `dbfread` does not follow x64 memo blocks, so the reference it compares
against has blank memo columns. **A harvest that resolves memo text can never
match it.** The comparison is harvest-versus-scaffold, not harvest-versus-engine.

    line 138     manifest_path = target / "HELP_META_EXPORT_MANIFEST_v0.csv"

Hardcoded **v0**. The sanctioned producer writes `HELP_META_EXPORT_MANIFEST_v1.csv`
with a different schema. Hence `manifest_findings=14` -- every file reported
"missing manifest row" while a complete, correct manifest sits beside it.

    line 92      if row.get("current_status", "").upper() != "EXPORTED":
                     findings.append(f"{target}: current_status is not EXPORTED")

Requires EXPORTED. The producer deliberately writes `CARRIED_STALE_MAY` for the
four META_* tables whose sources are not current -- the honest label. Even with
the filename fixed, four rows would still be reported as findings **for being
truthful**.

## The part that matters most

**v8's own wrong-producer promotion scored `E5 PASS: 14/14`.** It passed
*because* it was blank in exactly the way the checker's reference is blank. Two
identically-broken renderings agreeing with each other.

So the gate did not merely fail to catch the mistake. It certified it, and would
have gone on certifying it: every future run using the scaffold gets a green,
every run using the engine gets a red, and the red is the correct artifact.

This is the north star's failure signature at the producer/consumer seam --
except the copied fact here is a *rendering*, and the check that should have
crossed the span instead re-typed one side of it.

## Secondary: the producer's own row_count is wrong for memo tables

`HELP_META_HARVEST_EXPORT_v1.ps1` computes:

    function Csv-RowCount([string]$path) {
      $n = (Get-Content -LiteralPath $path | Measure-Object -Line).Lines
      if ($n -gt 0) { return $n - 1 } else { return 0 }
    }

That counts LINES, not CSV records. With memo text now resolving, quoted fields
contain newlines. Measured on `HELP_HELP_TOPIC.csv` from this run:

    manifest row_count        1196
    CSV records (proper parse) 666      <- and the engine transcript agrees:
                                           "Exported 666 records"
    physical lines            1356

**The counting is line-based rather than record-based, and that much is certain.
The exact arithmetic is NOT established:** 1196 is neither 666 nor 1356 minus
one, so `Measure-Object -Line` is not doing plain physical-line counting either
(CRLF handling, embedded CR, or a trailing-line rule are all candidates). A first
draft of this section asserted "LINES minus one" and that does not reproduce.

Recorded this way deliberately. The defect is proven -- a manifest column that
says 1196 where the file holds 666 -- and the mechanism is measured only as far
as it was actually measured. Whoever fixes it should confirm the arithmetic on
Windows PowerShell rather than inherit a guess from here.

Only the manifest column is wrong; the CSV itself is correct. It was invisible
before because the scaffold's blank memos contained no newlines -- **the bug
appeared the moment the export started being right.**

## What this does NOT change

    E5's requirement is sound. The canonical harvest SHOULD match current
    HELP/META. What is broken is the instrument, not the condition.

    The engine export at HELPMETA-20260902T012620Z is, on the evidence,
    the CORRECT artifact: right row counts, memo text resolved, honest
    CARRIED_STALE_MAY labels, per-file SHA-256.

## FIXED 2026-09-02 -- all four bindings, plus the producer bug

Four bindings to the scaffold, not one. Each was found by chasing the next
mismatch rather than assuming the first explanation was complete.

    1. MEMO COLUMNS      excluded from the comparison; the reference cannot
                         render them, so it must not judge them. A new
                         `memo_rendering` field reports RESOLVED (engine) vs
                         BLANK, so provenance is STATED instead of silently
                         rewarded.
    2. MANIFEST SCHEMA   v1 preferred over v0; CARRIED_STALE_MAY accepted as
                         the honest label it is, and its row_count check skipped
                         (it describes the carried file, not the live source).
    3. NUMERIC PADDING   both sides stripped. The engine preserves DBF
                         fixed-width ('       337'); dbfread strips. The
                         reference was ALREADY stripped for every column, so no
                         distinction was ever observable -- this removes a
                         penalty, not a check.
    4. ENCODING          `_recode()` round-trips latin1 -> bytes -> utf-8. dbfread
                         decodes latin1 and never raises, so it silently
                         mojibaked the UTF-8 the store actually holds.

    5. PRODUCER BUG      `Csv-RowCount` in HELP_META_HARVEST_EXPORT_v1.ps1 now
                         uses `Import-Csv | .Count` instead of counting physical
                         lines.

### Proof, both directions

    engine export HELPMETA-20260902T012620Z   14/14 tables match
    stale canonical harvested/                 9/14 -- real staleness STILL caught
    memo-blank scaffold candidate             13/14 -- now FAILS on the mojibake
                                                       row. The inversion is
                                                       reversed, not merely
                                                       removed.
    tampered non-memo value                    CONTENT_MISMATCH, row 2
    deleted row                                CONTENT_MISMATCH, row 6

    unit tests: 10 pass in this file, 18 across the harvest tools.
    Six new cases guard each fix, including an explicit regression test named
    for this inversion.

### The producer fix, measured before and after

Only ONE table was ever affected -- verified across all ten exported tables:

    csv                       manifest  records   source
    HELP_HELP_TOPIC.csv           1196      666      666   <- the only wrong row
    (all nine others)             match    match    match

Simulated the fixed `Csv-RowCount` output on a COPY of the run:

    E5 PASS: 14/14 tables match current HELP/META; manifest_findings=0
    exit 0

**So E5 clears on one host command.** Re-run
`HELP_META_HARVEST_EXPORT_v1.ps1` with the fixed script; it writes 666 and the
gate goes green on its own evidence.

**The PowerShell change is WRITTEN, NOT RUN.** There is no `pwsh` in this
sandbox. `Import-Csv` is the idiomatic record-wise count and handles quoted
embedded newlines, but confirm it on the host before trusting it -- the
prediction above is arithmetic, not an execution.

## The ruling this needs

Three candidate fixes, and they are not equivalent:

  (a) **Teach the checker the engine's rendering.** Its source side must resolve
      memo blocks the way `EXPORT ... CSV` does, and it must read
      `MANIFEST_v1.csv` and accept `CARRIED_STALE_MAY`. Largest change; makes the
      gate measure the right thing.
  (b) **Make the checker compare harvest-to-harvest** against a freshly
      engine-exported reference rather than re-deriving one in Python. Removes
      the second rendering entirely, which is this lane's own thesis.
  (c) Retire `export_help_meta_harvest.py` and its `_cell` as the reference
      implementation, keeping it only as a fallback the checker never trusts.

(b) is the move the lane keeps arguing for: stop maintaining a second renderer
and derive from the one that already exists. (a) makes the copy permanent by
teaching it a second dialect.

**Also owed:** fix `Csv-RowCount` to count CSV records, not lines. It is four
lines of PowerShell and it currently misreports every memo-bearing table.

## HOST-VERIFIED 2026-09-02 -- the fix executed, and the prediction held

The owner re-ran the fixed producer. New run `HELPMETA-20260902T112853Z`:

    E5 PASS: 14/14 tables match current HELP/META; manifest_findings=0
    exit 0

    HELP_HELP_TOPIC.csv row_count = 666        (was 1196; engine says 666)

**`Import-Csv` is now executed, not predicted.** The earlier simulation said
this exact result; the host confirms it. Every caveat about the PowerShell
change being written-not-run is discharged.

Both instrument bindings and the producer bug are closed:

    checker    memo columns / manifest schema / numeric padding / encoding
    producer   Csv-RowCount counts records

## Status of E5 for this run

    THE INSTRUMENT AND THE PRODUCER ARE FIXED.
    E5 IN ITS PHASE 8 FORM IS STILL NOT MET, AND THAT IS NOT A TECHNICALITY.

    export run  HELPMETA-20260902T112853Z   14/14  PASS
    canonical   harvested/                   9/14  FAIL

The Phase 8 entry check is explicit about which one it reads (plan, E5 row):

> Run `check_help_meta_harvest_freshness.py` against **the canonical
> `harvested/` workspace**. It must report 14/14 ... **A current candidate proves
> export readiness, not canonical readiness.**

The producer deliberately writes an immutable `export_runs/<run>/` and never
overwrites `harvested/`. So a correct export existing is necessary and not
sufficient: **promotion of that run to canonical is M-1, and M-1 still needs its
own GO.**

This is the same wall v8 hit before, and it is worth being blunt about why the
distinction is being honoured this time rather than argued around. The first
attempt cleared E5 by hand-copying over `harvested/`, which relabelled four
stale tables as current and scored a PASS the gate had no business giving. The
condition was never the problem. Reaching for the PASS was.

    v8 promotes nothing. Canonical remains as rolled back.
    E5 clears the moment M-1 is granted and that run is promoted.

    The gate now measures the right thing: the engine export reads 14/14, the
    stale canonical still fails 9/14, and the memo-blank scaffold now fails
    where it used to pass. Any E5 PASS from here means "matches current
    HELP/META", which is what the condition actually says.

    REMAINING, and it is one command:
      pwsh -File dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1
      -> writes a new run with row_count 666, and E5 goes PASS on its own
         evidence (simulated: manifest_findings=0, exit 0)

    THEN, and only then, promotion of that run to canonical is M-1 and still
    needs its own GO. v8 has promoted nothing. The rolled-back state stands.

## Non-ASCII in shipped HELP data -- exposed, not fixed

The encoding fix surfaced 28 HELP_LINE rows carrying non-ASCII, all traceable to
`src/help/helpdata_messages.cpp`:

    ZAP_ROLLBACK_FAILED_TEXT        "  Rollback also failed - manual recovery needed!"
    PACK_ROLLBACK_FAILED_TEXT       "  Rollback also failed: {detail} - manual ..."
    (plus header-count warnings, memo-object warnings, and PSHELL grouped-help
     rows using a right-arrow glyph instead of ->)

The em-dash and arrow glyphs are the ones quoted; the house rule is ASCII with
`--` and `->`. These are ERROR messages a user sees, and the cookbook already
warns that source em-dashes render as a CP437 garble in a runtime transcript.

`check_help_meta_harvest_freshness.py` now counts these per table
(`non_ascii_rows`) so they are reported rather than normalized away. **Not
fixed here**: it is a source edit to shipped message text, it needs a HELP
rebuild to take effect, and it is its own change with its own review.
