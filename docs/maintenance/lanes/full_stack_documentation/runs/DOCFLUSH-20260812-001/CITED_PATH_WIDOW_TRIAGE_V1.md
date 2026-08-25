# Cited-path widows -- twelve surfaced, eleven trackable, one that must stay broken

    Run    : DOCFLUSH-20260812-001 (flush v5), tidy-up
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Cause  : `c76d9ef60` put `AI_INTERACTION_INTAKE_QUEUE_V1.md` and
             `coordination/OPEN_ITEMS.md` in a change set, so `cited-paths`
             checked all 355 paths those two registers cite. 343 tracked.
    Status : review-needed. Twelve are a `git add` plus a 19-character ASCII
             normalization; one is not, and should not be.

---

## 1. What this is not

**No new drift. Nothing broke.** These citations have been there for weeks; the
gate only inspects documents in the change set, so touching the two big
registers is what made their whole citation surface visible at once. The same
mechanism surfaced the MANHASH widow yesterday, and that one is now closed
because the accepted catalog was tracked first.

**Volume is the finding, not severity.** 12 of 355 is 3.4 percent, and every one
of the eleven is a real authored artifact sitting on disk in a fresh clone's
blind spot.

---

## 2. The eleven -- all stageable, none ignored

`git check-ignore` returns nothing for any of them, so "an IGNORED path can
never be staged at all" does not apply here. Total 81,151 bytes.

    bytes   oldest-first
    2,422   dottalkpp/help/find_repo_string.ps1                       2025-12-15
    4,791   dottalkpp/data/schemas/mcc_x64_output.txt                 2026-03-29
    1,458   docs/cases/CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB.md      2026-06-28
    3,690   dottalkpp/data/scripts/suites/table_buffer.dts            2026-07-06
   10,536   docs/agents/HANDOFF_CLAUDE_MESSAGING_CORRECTIVE_AUDIT_2026-07-16.md
   12,778   docs/maintenance/DotScript_Arrays_Catalog_v1.json         2026-07-20
   25,022   .../runs/DOCFLUSH-20260722-001/FULLSTACK_DOCUMENTATION_FLUSH_COMPLETE_HANDOFF_V1.md
    5,128   docs/maintenance/CASCADE_ERP_GATE0_HOUSEKEEPING_V1.md     2026-08-10
   14,701   docs/maintenance/DOTTALKPP_LABTALK_DATABASE_ECOLOGY_INVENTORY_V1.md
      765   dottalkpp/data/scripts/fieldtype/vfp_types_make.dts       2026-08-12
      760   dottalkpp/data/cdxdemo.dts                                2026-05-29

**All eleven classify as SOURCE, not data** -- checked against the gate's own
`is_data_fixture()` rather than guessed. `.dts`, `.txt`, `.json` and `.ps1` are
not in `DATA_SUFFIXES`, and none sits under a `DATA_DIR_SEGMENTS` prefix
(`/data/dbf/`, `/data/indexes/`, `/data/lmdb/`, `/data/help/`, `/data/metadata/`,
`/data/manuals/`). `dottalkpp/data/scripts/` and `dottalkpp/data/schemas/` are
outside every one of them. **No `X64BASE_ALLOW_DATA` is needed.**

They are all authored artifacts, not churn: two carry structured front matter
(an `ai-report-audit-v1` block; case id `ENG-010`), two are lane ledgers with
status headers, one is a JSON schema catalog, one is a 25 KB flush handoff, four
are `.dts` fixtures and suites, one is a PowerShell search helper.

### 2a. Two judgement calls inside the eleven, flagged not hidden

- **`dottalkpp/data/schemas/mcc_x64_output.txt` is a captured error transcript**,
  not source: it opens `SCHEMAS LOAD: cannot read file: ...`. Tracking it
  preserves evidence a register cites; it is still an output capture, and if the
  maintainer would rather registers cite reproducible inputs than saved
  failures, this is the one to drop.
- **Two files carry absolute machine paths.** `cdxdemo.dts` opens
  `SET PATH DBF "D:\code\ccode\docs\datadict\..."` and the transcript above
  names `D:\code\ccode\dottalkpp\...`. Tracking bakes one workstation's layout
  into history. That is already true of the citation; tracking makes it
  permanent. Not blocking, worth knowing.

---

## 2b. THE FIRST ATTEMPT WAS BLOCKED, and the block was correct

Staging the eleven failed the gate with **exit 2, a HARD block** -- not the
advisory above. Cause: `house-style`.

**Tracking an old document runs it through today's house style for the first
time.** Every line of a newly added file is an added line, so the ASCII rule
meets the whole file at once. Three of the eleven carried non-ASCII that had
never been staged and therefore never been checked:

    16 chars   .../DOCFLUSH-20260722-001/FULLSTACK_DOCUMENTATION_FLUSH_COMPLETE_HANDOFF_V1.md
     1 char    docs/agents/HANDOFF_CLAUDE_MESSAGING_CORRECTIVE_AUDIT_2026-07-16.md
     2 chars   dottalkpp/data/scripts/suites/table_buffer.dts
    --------
    19 total

Every one is cosmetic and none is in a command, path, literal or datum:
seventeen em dashes in headings and table cells (`Gate 0 -- status`,
`0 -- mission/baseline`), and two right single quotes inside `*` comments in the
`.dts` (`you've`, `doesn't`). Normalized `--` and `'` per house rule. Line counts
unchanged: 219, 706 and 126 before and after. All twelve staged files are now
zero non-ASCII.

**This edits dated historical records, and that is worth saying out loud.** The
July handoff now differs by 16 bytes from what its author wrote. The alternative
was to leave evidence a tracked register cites outside version control. Pre-edit
copies are in gitignored `tmp/*.preascii` for the length of this session only; the
authoritative before-state is the untracked file's absence from history, which
is the problem being fixed. **If the maintainer would rather historical
handoffs keep their bytes, the answer is to stop citing them from a tracked
register, not to track them unnormalized** -- the gate will block it either way.

## 2c. A twelfth file, and why the list grew while being fixed

The blocked run also surfaced:

    WIDOW docs/maintenance/database_ecology/SIDECAR_INTAKE_CANDIDATE_DBECO-20260810-001.csv
          cited by docs/maintenance/DOTTALKPP_LABTALK_DATABASE_ECOLOGY_INVENTORY_V1.md

**That citation was invisible until the inventory entered the change set.**
`cited-paths` inspects only documents being committed, so the citation graph is
explored ONE HOP AT A TIME: track a document, and its own citations become
visible on the next run. Widow triage converges by iteration, not in one pass,
and a run that ends with fewer widows than it started is making progress even
when the count does not reach zero.

Included here rather than deferred, which closes this hop: 89,898 bytes, 240
rows, ASCII, not ignored, source lane. It is the sidecar intake candidate ledger
the inventory cites -- **and it carries `GIT_TRACKED` and `GIT_IGNORED` columns,
so it is a ledger recording which files are tracked that was not itself
tracked.**

Twelve files, 171,049 bytes.

---

## 3. The last one cannot be fixed, and that is correct

    MISSING docs/getting-started/BUILDING.md -- cited, not on disk
            cited by coordination/OPEN_ITEMS.md
            cited by THIS DOCUMENT, as of the blocked run

**And this document now trips it too.** Naming the path in order to explain why
the path may not be named is not a joke at the gate's expense -- it is the
cleanest possible demonstration of 3a below. A register documenting a broken
citation is indistinguishable, to a path checker, from a register containing
one.

**The citation is the finding.** It comes from `OI-010`, whose entire subject is
that this path exists on one branch and not the other:

    main carries TWO build documents and development carries one; decide which
    is canonical before a third diverges. Measured 2026-08-17: origin/main has
    both BUILDING.md and docs/getting-started/BUILDING.md; development has only
    the root one, and the public README links the docs/getting-started/ copy.

Confirmed here: `git ls-files` on `development` lists root `BUILDING.md` and six
`BUILDING.dbf`/`.cnx`/`.cdx` data tables, and no `docs/getting-started/BUILDING.md`.
`docs/getting-started/` holds three files and that is not one of them.

**Neither remedy the advisory offers is right.** Creating the file would
fabricate the second copy OI-010 exists to prevent. Removing the citation would
delete the measurement that makes the row actionable.

### 3a. The shape, since this is the sixth time today

`cited-paths` cannot distinguish **"this document cites a path that is broken"**
from **"this document's subject IS that the path is broken."** It is right about
the fact and wrong about the implication. That is the inverse of the day's other
findings: not a check that cannot fail, but a check that cannot tell a report
from an offence.

Same remedy family as AIF-118's corollary -- **judge the subject against its own
declaration.** `refcheck_v1` accepts an empty catalog for `status: reserved` and
fails it for `status: supported`. A row that is ABOUT a missing path could
declare so, and the gate could read the declaration instead of a hand-kept
allow-list. **Not proposed as work here** -- it is a gate change, it belongs to
AIF-100 (gate governance), and one advisory line is a very cheap problem.

**Recommendation: leave it.** The advisory is not blocking, it is accurate, and
it disappears the day OI-010 is decided. Its presence is a standing reminder
that the decision is open, which is what `OI-010` is for.

---

## 4. Good Neighbour

    What changed      : this document. The eleven files are handed to the
                        steward to stage; nothing was staged here.
    Whose area        : the two registers are shared and were read only. The
                        eleven span docs/agents, docs/cases, docs/maintenance
                        and dottalkpp/ -- adding, never modifying.
    What authorization: the cited-paths advisory raised by `c76d9ef60`.
    How to verify     : `git check-ignore` returns nothing for all eleven;
                        `python -c "import prepush_gate; is_data_fixture(p)"`
                        returns False for all eleven; after staging,
                        `git ls-files` lists them and the advisory drops from
                        twelve entries to one.
    How to undo       : `git rm --cached` on the same eleven paths; the files
                        stay on disk either way.
