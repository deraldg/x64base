# Phase 6 -- the manualgen accepted catalog, opened and verified

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Method : read-only. Thirteen DBF headers parsed, every declared artifact
             re-hashed against disk. No engine, no build, no mutation.
    Status : **review-needed.** ONE item needs a maintainer decision (S6).
             S5 is WITHDRAWN -- see section 0.

---

## 0. CORRECTION, same day -- the drifted artifact is NOT the manual

This document was written before the accepted pointer evidence was read, and
section 4 (S4) overstates what the drift means. **`media_section_v1` is a
SUPPORTING PUBLICATION WORKSPACE, not the manual.** The manual is
`developer_manual_publication_v1`, recorded three times before this run began:

    accepted_artifacts/ACTIVE_PRIMARY_READER_ARTIFACT.txt        2026-06-03
    published/README.md                                          2026-07-09
      -- media_section_v1 listed under "Supporting publication workspaces"
      -- "Do not assume the newest lane is the promoted lane."
    review_packets/MDO-295E_..._SELECTION_DIAGNOSIS_PACKET.md    score 344 vs 45

**The actual manual is byte-intact.** Against
`accepted_artifacts/primary_reader_artifact_v1.json` (accepted 2026-07-28):
sha256 MATCH, 4,118 lines MATCH, 237 headings MATCH, and its 183 section
command links resolve 183 of 183.

So S4 stands as a measurement and falls as an alarm: a workspace drifted, which
is what a workspace does. **S5 and S6 below are withdrawn as posed** -- see
sections 4a and 5a. The rest of this document (the header arithmetic, the
MANSECTION re-hash, S1/S2/S3, the MANHASH read) is unaffected and stands.

Corrected measurement and the prior-art scan:
`PHASE6_REHARVEST_DEBT_V1.md`, sections 0 through 5.

---

## 1. Headline

**The accepted catalog is 90 days old and has held. Twelve of thirteen hashed
artifacts are byte-identical to their accepted values. The one that drifted is
the published developer manual -- the only artifact in the catalog a reader
actually opens.**

And the table that records that fact is `MANHASH`, the one table the project's
own reader could not open (AIF-127). **The reader defect was not merely
inconvenient: it was sitting on top of the catalog's only real failure.**

---

## 2. What was opened

The catalog is bigger than the eight tables Phase 6 started from. There are
**two** accepted catalogs, and both are x64 (`0x64`), so the documentation-
database house rule holds without exception here:

    man_catalog_v1              generated 2026-05-27   8 tables
      MANRUN        3 rows      MANSECTION   25 rows
      MANPUB        4 rows      MANREVIEW     3 rows
      MANAPPX       6 rows      MANMEDIA      9 rows
      MANANCHOR     9 rows      MANHASH      13 rows   <- AIF-127

    manstar_native_reference_v1 generated 2026-06-06   5 tables + 5 CDX
      MANREFRUN     1 row       MANREFPTR     1 row
      MANREFART     8 rows      MANREFGATE    8 rows
      MANREFHASH   24 rows

**Every one of the thirteen files reconciles exactly by header arithmetic**
(`hdrlen + nrec x reclen + 1 == size on disk`), with no exceptions. Nothing in
this catalog is damaged.

`manstar_native_reference_v1` was not in the Phase 6 inventory and should be.
It is ten days newer than `man_catalog_v1`, it is the only part of the catalog
carrying **CDX indexes**, and its `MANREFHASH` holds 24 hash rows against
`man_catalog_v1`'s 13.

---

## 3. MANSECTION -- 25 sections, 24 verified

Re-hashed every `RELATIVE_P` against disk:

    hash match   24
    drift         0
    unresolved    1   (MANSECTION-025, see S1)

Twenty-four authored section files, written 2026-05-27, are **byte-identical
90 days later**. The section body of this manual is stable.

### S1 -- `RELATIVE_P` holds two kinds of address, and only one is a path

MANSECTION-025 initially read as MISSING. It is not missing. Its `RELATIVE_P`
is not a file path:

    docs\...\developer_manual_publication_v1_media_section_v1.md#why-media-needs-an-anchor-manifest

Twenty-four rows hold a **file path**; one holds a **file path plus a fragment
anchor**. `os.path.exists()` is a correct test for the first kind and a
guaranteed false negative for the second. Any consumer that treats the column
uniformly reports a healthy catalog as broken -- which is what happened here,
for about ninety seconds, until the value was read rather than tested.

The column cannot answer "is this section on disk" because it is answering two
different questions. That is the R5 shape (**one question, two answers**) in a
schema rather than in code, and it is the same defect class as AIF-126.

**Not a data error. A column that needs a companion -- a kind discriminator, or
the anchor split into its own field.** MANANCHOR (9 rows) exists and may already
be the right home; that is the design call.

### S2 -- `sections/sections/`

Twenty-three of twenty-five paths carry a doubled segment:

    .../developer_manual_publication_v1_media_section_v1/sections/sections/<slug>.md

One sits at `.../sections/<slug>.md` and one at the publication root. The
doubling is REAL on disk -- those 23 files hash-matched, so this is how the tree
is laid out, not a catalog typo. Cosmetic, consistent, and worth knowing before
anyone writes a path-repair pass that "fixes" it and breaks 23 verified rows.

### S3 -- `LENGTH_BYT` is declared and almost never written

`MANSECTION.LENGTH_BYT` is `N(18)` and is **blank in 25 of 25 rows**.
`MANHASH.LENGTH_BYT` is `N(18)` and is blank in **12 of 13** -- MANHASH-003
alone carries `765`.

A numeric column that is blank everywhere cannot distinguish "not measured"
from "zero bytes", which is the AIF-118 shape. It is also the cheapest possible
corroborating check on a hash and it is being paid for in every record and never
collected. One populated row out of thirty-eight is worse than none: it makes
the column look functional.

---

## 4. MANHASH -- what AIF-127 was hiding

Read with a one-off parser that locates the `X64M` marker POSITIVELY instead of
deriving it from the `0x0D` terminator. Field table reconciles
(`sum(widths) + 1 == reclen`), so the read is trustworthy:

    HASH_ID C(19) | ARTIFACT_R C(56) | RELATIVE_P C(151) | SHA256 C(72) | LENGTH_BYT N(18)

Re-hashed all thirteen:

    MANHASH-001   HASH-DRIFT   developer_manual_publication_v1_media_section_v1.md
    MANHASH-002   MATCH        mdo_243_status_summary_v1.csv
    MANHASH-003   MATCH        mdo_244_status_summary_v1.csv
    MANHASH-004   MATCH        mdo_244_candidate_table_plan_v1.csv
    MANHASH-005..013 MATCH     nine storyboard PNGs under docs\media\

    match 12   drift 1   missing 0

### S4 -- the published manual drifted from its accepted hash, and the timestamps say when

    accepted (MANHASH-001)  5C45339E6DF0406913092991E85A37FAD77A03B5C241E0C53EB5DB89543F923A
    on disk today           5ADFCDED44B4C7F4B0938EAC526FA466A5C4BB48FD59BFC85DA582E91E7F2C53

    catalog promoted        2026-05-27 14:47:38Z   (man_catalog_v1_manifest.json)
    publication written     2026-05-27 19:13:55Z   (mtime)
                            -------------------
                            4h 26m AFTER acceptance, same day

The manifest records `"publication_replacement": 0` -- **the promotion did not
touch the publication.** Something else did, four and a half hours later, and
the catalog was never re-accepted.

**The change appears to be an addition, not damage.** The publication now
carries two top-level sections the accepted section list does not:
`MAN* Catalog and Manualgen CLI Visibility Reference` and `Manual Mutation Cycle
and Guarded Publication Workflow`, 5,861 bytes at the tail. 19 of the 23
non-blank lines of
`runs/DOCFLUSH-20260716-001/manualgen_phase/overlay_candidate_v1/mdo_261_man_cli_visibility_reference.md`
appear verbatim in the publication, so the overlay material and the publication
tail are the same body of text. **Which way the copy went is NOT established by
this pass** and should not be assumed: the overlay candidate file is dated
2026-07-17, seven weeks after the publication was last written, so the overlay
may equally have been extracted FROM the publication.

**The important part is not the cause. It is that the catalog has asserted a
stale hash for its headline artifact for ninety days and nothing said so** --
because the assertion lives in the one table the reader declines to open.

### S5 -- WITHDRAWN. See section 4a.

### 4a. What S5 becomes

S5 asked whether to re-accept or revert the drifted publication. The question
assumed the drifted artifact was the manual. It is not.

`MANPUB-001 ROLE=active_publication` naming `media_section_v1` while the reader
pointer names `developer_manual_publication_v1` is **known and intentional**.
`SESSION_CLOSEOUT_MANUAL_POINTER_EVIDENCE_RECONCILIATION_2026-07-18.md` records
a pointer audit of 21 PASS, 1 REVIEW, 0 FAIL and names the one retained REVIEW:

    "intentional MDO-350E controlled-publication versus active
     primary-reader role split"

**Do not re-accept the catalog to chase workspace drift, and do not re-point
MANPUB.** Both would be work against a supporting workspace.

What survives, with a date on it: the catalog was promoted 2026-05-27 and the
reader pointer was decided 2026-06-03. **The catalog is a correct record of a
state that changed seven days later, and nothing has re-run it since.** That is
staleness, not contradiction, and it is the reason a stale MANHASH-001 hash sat
unremarked for ninety days.

## 5. Tracking -- the widow is a known residual, already measured

The commit gate raised:

    WIDOW .../accepted_catalogs/man_catalog_v1/dbf/MANHASH.dbf
          -- on disk, NOT tracked, cited by AIF127_FINDING_X64_FALSE_TERMINATOR_V1.md

**MANHASH is not special. NONE of `accepted_catalogs/` is tracked**, and this is
not new information -- `OI-011` measured it on 2026-08-18 and named the exact
remainder: *"leaving residual exposure of 38 files / 0.07 MB in
`accepted_catalogs`"*. Only MANHASH raised an advisory because only MANHASH got
cited by a document.

Re-measured today, after `manualgen/**/*.csv` took 15 of them:

    files under accepted_catalogs   39
    gitignored                      15   (the mdo_* CSVs)
    residual, untracked, NOT ignored 24   58,873 bytes

The 24 are the two catalogs' 13 DBFs, 5 CDX indexes, 4 acceptance summary `.md`
files, the `man_catalog_v1_manifest.json`, and the tree `README.md`.

### S6 -- still open, and unaffected by the correction above

Tracking the 24 residual accepted-catalog files is a separate question from
which publication is the manual, and the correction does not touch it. OI-011
already answered the general case for the authored half -- *(a) intended to be
tracked and never were*. This is 58 KB of promoted, gated, manifest-carrying
baseline that a `git clean -fd` would take with no history to recover from.

Recommended: track all 24 as explicit paths, which also retires the WIDOW
advisory at its cause rather than by editing a citation out of a finding.
PowerShell handed to the steward separately.

## 6. What this pass did NOT do

- **AIF-127 is still NOT FIXED.** The one-off parser used here wrote nothing and
  is not committed. `tools/fullstack_docs/dbfread.py` still cannot open a table
  whose row count carries `0x0D` in its low byte.
- No re-harvest debt was measured. That is the next piece of Phase 6: the manual
  candidate predates its own HELP rebuild and lacks BBS/NET/CANARY/CMDREL/
  FORMULA/EDIT, while the store has since gained APPGUI, GUI, SMTP, lost five
  function-phantoms, and gained 139 owner topics (AIF-126).
- Nothing was mutated, promoted, re-accepted or staged.

---

## 7. Good Neighbour

    What changed      : one new document (this file) and one intake row
                        (AIF-127) in docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md.
                        No code, no catalog, no publication.
    Whose area        : full_stack_documentation lane (mine). The catalog and
                        the publication belong to manualgen and were READ ONLY.
    What authorization: flush v5 Phase 6, "run through manual gen".
    How to verify     : re-hash any MANSECTION RELATIVE_P or MANHASH RELATIVE_P
                        against its stored SHA256. MANHASH needs the X64M
                        positive-locate workaround until AIF-127 is fixed.
    How to undo       : delete this file; remove the AIF-127 row.
