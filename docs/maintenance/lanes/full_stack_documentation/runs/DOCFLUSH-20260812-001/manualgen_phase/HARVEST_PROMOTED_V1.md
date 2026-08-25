# The harvest is promoted -- 34 to zero, and one verification that was nearly stale

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    Lane   : **AIF-068 `manualgen-harvest-feeder`**
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Auth   : the owner's "promote the harvest" -- the gated act named in the
             input contract's authority boundary.
    Status : **DONE and verified.** One check must be re-run by the steward
             under `$py12` before this is called authoritative (section 5).

---

## 1. The check that had to come first, and it passes

Section 3a of `HARVEST_REFRESH_CANDIDATE_V1.md` said the two additive columns
(`DEF_LOCALE`, `REGION_ID`) are safe for a consumer reading columns BY NAME and
unsafe for one reading BY POSITION, and that this wanted checking rather than
assuming. Checked, before anything was copied.

**Every data consumer of the harvest reads by name.** Ten readers touch these
files. Nine use `csv.DictReader`. The single `csv.reader` is
`manualgen_lib/harvest.py:49` `_csv_shape()`, which reads the header as a LIST
OF NAMES to report `column_count` and then counts rows -- **it never indexes a
data row by position.** A tree-wide search for `row[0]`-style indexing or manual
`split(",")` over these files returns nothing.

Two added columns are therefore safe. Had that search found one positional
reader, this promotion would not have happened today.

## 2. What was replaced, and what was not

    replaced   the 14 contract CSVs + HELP_META_EXPORT_MANIFEST_v0.csv
    untouched  harvested/README.md, harvested/export_runs/

The outgoing set is preserved at
`manualgen_phase/harvested_preexisting_20260825/` (15 files), so the promotion
is reversible by copying it back. Digest of the outgoing set, for the record:

    sha256 of the sorted per-file sha256 list:
    7cb2ba74f586ab980ae79f9ab1c12cc35c27aa62f338161c13e04f4f86bfe246

## 3. Verified

**The canonical harvest now equals the candidate exactly.**
`compare_help_meta_harvest.py --baseline <candidate> --candidate <harvested>`:

    required 14   unchanged 14   compatible content 0   header changed 0
    missing 0     rows 62,538 -> 62,538

**The debt is zero, measured the same way it was first measured.** Canonical
harvest against the live HELP store, on `COMMAND`:

    canonical harvest distinct names   320
    live store distinct names          320
    LIVE BUT NOT IN THE HARVEST          0
    IN THE HARVEST BUT NOT LIVE          0

The 34 are closed and the three stale renames (`SETNEAR`->`SET NEAR`,
`SIMPLEBROWSE`->`SIMPLEBROWSER`, `SMARTBROWSE`->`SMARTBROWSER`) are retired,
along with `VUSE`, the only command that actually left the surface.

**manualgen's own validate**, run today at `MANRUN-20260825T121927Z-B70BDCF3`:

    selected_harvest_workspace=.../harvested  selection_mode=legacy_default
    files=14/14        boundary_fail_rows=0
    validation_fail_rows=1   validation_review_rows=2

All three are procedural, none is about harvest content -- see section 5.

## 4. THE VERIFICATION I NEARLY REPORTED WAS TWENTY DAYS OLD

`reports/mdo_226_inventory_harvest_v1.csv` shows a clean 14/14 PASS with row and
column counts, and it was about to be quoted here as proof the promotion
validates. **It is dated 2026-08-05.**

`validate` writes `mdo_226_validate_*`; only `inventory` writes
`mdo_226_inventory_*`. I ran `validate`. The inventory report is from a run
twenty days ago and describes the OLD harvest.

It was caught by the row counts disagreeing with the export by ones and
hundreds in BOTH directions -- 460 exported against 461 reported, 75 against 74
-- which is not a shape any off-by-one explains. The `stat` was the instrument;
the inference would have shipped a stale number as a fresh proof.

**This is the same defect class as the `__DATE__` build stamp and the EDREF row
count: a report that cannot say how old it is, read as though it were current.**
The counts in section 3 come from tools run today and re-derived from the files
on disk; none of them comes from a manualgen report.

## 5. WHAT THE STEWARD MUST RE-RUN, and why my run is indicative only

    PYTHON_312   FAIL   value 3.10.12   expected >= 3.12
                 "Manualgen requires Python 3.12 or newer."

**I ran manualgen on Python 3.10.** The house rule is that host Python goes
through `$py12`; the sandbox reaching this tree has 3.10 and no `$py12`. A tool
that declares it needs 3.12, run on 3.10, is the "a test in another language
tests a different program" shape, and I stopped rather than running `inventory`
as well and generating fresh-looking artifacts from the wrong interpreter.

**Nothing in section 3 depends on manualgen**: the comparison, the debt check
and the file digests are stdlib CSV and DBF reads. But the authoritative
`validate` and a current `inventory` want:

    & $py12 tools\manualgen\manualgen.py validate
    & $py12 tools\manualgen\manualgen.py inventory

The other two rows are REVIEW, not FAIL, and are the contract working as
designed:

    ASSEMBLY_SELECTION_EXPLICIT  REVIEW  legacy_default, expected explicit
    HARVEST_SELECTION_EXPLICIT   REVIEW  legacy_default, expected explicit

They say an evidence-bearing run must NAME its workspaces rather than inherit
the default. They are a property of how I invoked it, not of what was promoted.
An earlier run's report (`mdo_224`) carries the `PYTHON_312` FAIL and no REVIEW
rows, which is what naming the workspaces looks like.

## 6. What promotion did NOT do

- **No prose.** The contract is explicit that a passing selection proves which
  evidence was chosen, not that every changed row reached the 25 sections. The
  **21 written-debt commands are untouched** and remain the real content work.
- No pointer moved, no publication changed, no accepted catalog altered.
- **Nothing entered git.** `harvested/` is 61 files, **60 gitignored and 0
  tracked** -- `manualgen/**/*.csv` covers it. See section 7.

## 7. The canonical harvest exists only on this workstation

`git ls-files docs/manuals/developer/manualgen/harvested/` returns nothing, and
60 of its 61 files are ignored. **A fresh clone has no canonical harvest at
all.**

Unlike today's other untracked findings, **this one is a decision rather than an
omission** -- OI-011 reasoned that manualgen CSVs are regenerable output and
`manualgen/**/*.csv` was written deliberately. What has changed is that the
reasoning is now TRUE: in May the harvest was, in the exporter's own words, "a
hand-made May snapshot" with no producer. `export_help_meta_harvest.py` is
tracked, and this promotion is reproducible from the DBFs by running it.

**Recorded, not challenged.** The ignore rule earned its justification after the
fact, which is worth knowing the next time someone asks why the manual's
evidence is not in the repository.

## 8. Good Neighbour

    What changed      : the 15 canonical harvest files were REPLACED, in the
                        working tree only -- they are gitignored. Plus this
                        record and a preserved copy of the outgoing set.
    Whose area        : manualgen, under AIF-068. Both tools used are prior art
                        and were run, not modified. The HELP store belongs to a
                        concurrent session and was read through the shared
                        reader only.
    What authorization: the owner's explicit "promote the harvest" -- the act
                        the input contract names as separately gated.
    How to verify     : compare the harvest against the live store on COMMAND
                        (320 == 320, zero either way); or re-run
                        compare_help_meta_harvest.py against
                        harvest_candidate_20260825 (14 unchanged, 0 changes).
    How to undo       : copy the 15 files from
                        manualgen_phase/harvested_preexisting_20260825/ back
                        over harvested/. Nothing else moved, and nothing needs
                        reverting in git because nothing entered it.
