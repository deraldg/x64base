# Phase 6 -- the re-harvest debt, measured

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Method : read-only. Canonical harvest and accepted pointer evidence against
             the live HELP command registry. No engine, no build, no mutation.
    Lane   : **AIF-068 `manualgen-harvest-feeder`** (DOCFLUSH-20260722-001,
             claimed 2026-07-27). This document reports INTO that lane. It does
             not open a new one.
    Status : review-needed. **No maintainer decision is requested -- the two
             this document originally posed were already answered in the tree.**

---

## 0. FIRST DRAFT WAS WRONG. What this section corrects.

The first version of this document, written earlier the same day, led with
"the accepted publication has 163 command links and every one is broken" and
asked the maintainer to decide which publication is the manual.

**Both were mistakes, and they were the same mistake: I measured the artifact
without first looking for the decision about the artifact.** That is the
`docpush_preflight.py` failure repeated -- search for the name, not the purpose
-- three weeks after writing a hints section telling the next agent not to do
exactly this.

The answer was recorded in three places before I asked:

    accepted_artifacts/ACTIVE_PRIMARY_READER_ARTIFACT.txt        2026-06-03
      -> published/developer_manual_publication_v1/developer_manual_publication_v1.md

    published/README.md                                          2026-07-09
      "Primary reader artifact: developer_manual_publication_v1/..."
      media_section_v1 -> "Supporting publication workspaces"
      Policy: "Do not assume the newest lane is the promoted lane."

    review_packets/MDO-295E_PRIMARY_READER_ARTIFACT_SELECTION_DIAGNOSIS_PACKET.md
      score 344  developer_manual_publication_v1     role reader_candidate
      score  45  media_section_v1                    role candidate_needs_title_wrapper

The `published/README.md` policy line is aimed precisely at the error made
here. It was written seven weeks before the error.

---

## 1. The manual is intact

`developer_manual_publication_v1/developer_manual_publication_v1.md`, checked
against its own accepted evidence record
`accepted_artifacts/primary_reader_artifact_v1.json` (accepted
2026-07-28T04:19:31Z):

    artifact_sha256    EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F
    on disk            EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F   MATCH
    artifact_lines     4,118   on disk 4,118    MATCH
    heading_count        237   on disk   237    MATCH

**Zero drift.** Its 183 section command links resolve 183 of 183.

The page count is the one number that differs, and it reconciles exactly:

    accepted record          command_reference_pages   183
    COMPLETE_COMMAND_REFERENCE_INDEX_V1.md             191
       reader-linked 164 + supplemental 19             183   <- the accepted set
       post-baseline coverage-repair pages               8   <- added after acceptance
                                                       ---
                                                       191

Both numbers are honest and they count different things. The index says so in
its own header, and adds "this index does not conceal it."

**The drift reported in PHASE6_CATALOG_VERIFICATION_V1.md section S4 is in
`media_section_v1`, a supporting publication workspace, not in the manual.**
Workspaces drift; that is what a workspace is. See section 5.

---

## 2. The debt, in the lane's own units

AIF-068 already defines what a harvest is and where it lives.
`MANUALGEN_HELP_META_HARVEST_INPUT_CONTRACT_V1.md` binds a manualgen run to a
14-CSV HELP/META snapshot with per-file SHA-256, and names replacing
`docs/manuals/developer/manualgen/harvested/` as a separately authorized gate.

So the debt is not a prose count. **It is the distance between the canonical
harvest and the live store**, and it is one number:

    canonical harvest  harvested/HELP_COMMANDS.csv   403 rows / 290 names
                       written 2026-05-25 16:06      -- 92 days old
    live store         dottalkpp/data/help/COMMANDS.dbf
                       generated 2026-08-25          460 rows / 320 names

    LIVE BUT NOT IN THE CANONICAL HARVEST                34
    IN THE HARVEST BUT NOT LIVE                           4

### 2a. The 34

    APPGUI      ARCTICTALK  BBOX        BBS         BUILD INFO
    BUILD VECTORS  BUILDVECTORS  DDICT   DEFCMD      DEFFN
    EVALDIFF    EXIT        EXITS       EXPORTFUNCTIONS
    GUI         HANUKKAH    MAINT       MANSTAR     MANUAL
    MSGMGR      NET         QUIT        REGRESSION  SET CDX
    SET CNX     SET LMDB    SET NEAR    SMTP        STOP_ON_ERROR
    STRCAT      UNDEFCMD    UNDEFFN     USER        VDISK

### 2b. The 4

    SETNEAR   SIMPLEBROWSE   SMARTBROWSE   VUSE

Three are renames the harvest predates (`SETNEAR`->`SET NEAR`,
`SIMPLEBROWSE`->`SIMPLEBROWSER`, `SMARTBROWSE`->`SMARTBROWSER`). **Only `VUSE`
actually left the surface.**

**34 is the re-harvest debt.** It is a single gated action -- refresh the
harvest under the input contract -- not thirty-four separate writing jobs.

---

## 3. Prose coverage, and why it is a SECOND number

Measured against the primary reader artifact (28 sections, its appendices, its
assembled body, its 191 pages), the live 320 names fall out as:

    TIER 1  has a page, or is linked from a section list     193
    TIER 2  named in the body, no reference page              89
    TIER 3  absent entirely                                   38   (37 implemented)

**This is NOT the same quantity as section 2 and must not be added to it.** A
command can be in the harvest and still unwritten, or written and not yet
harvested. Of the 38 absent, 16 are also missing from the harvest (they will
arrive with the refresh) and 21 are IN the harvest and still unwritten
(refreshing the harvest will not touch them).

`MANUAL`, `DDICT`, `BBOX` and `MAINT` are documented in the primary artifact as
prose -- MDO-381E records that alignment as a completed milestone. The first
draft of this document listed all four as absent, because it was reading the
workspace.

### 3a. The 21 written-debt commands, and the hypothesis that is now refuted

    AVERAGE  BOOLEAN  BROWSETUI  BROWSETV  DISPLAY  ECHO  FIRST
    FORMULA  INDEXSEEK  LAST  LIST_LMDB  NEXT  PRIOR  RBROWSE
    REFRESH  REL_LIST  SIMPLEBROWSER  SMARTBROWSER  SORT
    TRANSFORM  WHERECACHE

The first draft proposed that `FIRST`/`LAST`/`NEXT`/`PRIOR` going missing
together "looks like a generator boundary, not independent oversights."

**The harvest contract refutes that in its own words:**

    "The 25 selected manual section hashes remain unchanged, proving the
     existing prose assembly is not yet a harvest-driven transformation."

The sections are AUTHORED, not generated. There is no generator to have a
boundary. These 21 are unwritten prose, and the quartet clustering is a writer's
omission rather than a tooling artifact. **A tidy hypothesis that survives only
until you read the contract governing the thing it explains.**

### 3b. TIER 2 is mostly not debt, and one number to keep

TIER 2 is dominated by SET-family variants and aliases the manual handles
deliberately in `review_and_deferred_set_family.md` and
`review_and_deferred_alias_and_variant_review.md`. **A first cut that counted
page-existence alone reported the debt as 114.** Page-existence is a proxy that
cannot answer "is this documented"; it inflated the number by about seventy
percent. Same family as the `__DATE__` build stamp and the EDREF row count.

---

## 4. Prior art found on a scan of the AIF register

Run after the fact, at the owner's instruction, and it should have been run
first. Six adjacent lanes exist:

    AIF-068  manualgen-harvest-feeder          THIS LANE. Owns the harvest
                                               contract and the feeder.
    AIF-072  docflush-manual-web-ascent        Phase 7 pickup; the manualgen
                                               published tree, accepted-not-deployed.
    AIF-088  command_catalog_runtime_drift     catalog vs runtime drift, found on
                                               R-APPEND-BLANK -- a TIER 2 member here.
    AIF-092  publication-surface-recovery      the publication surface.
    AIF-114  set-family-doc-drift              seven SET options PUBLISHED WITH NO
                                               IMPLEMENTATION. Exact mirror of the
                                               SET CDX/CNX/LMDB/NEAR entries here,
                                               which are implemented and unpublished.
    AIF-066  locale spine                      "manuals greenfield".

**Nothing here needs a new AIF.** The measurement belongs to AIF-068 and the
SET-family half is a second face of AIF-114.

---

## 5. The MANPUB role split is KNOWN and INTENTIONAL

An earlier note in this run called it an R5: `MANPUB-001 ROLE=active_publication`
points at `media_section_v1`, while the reader pointer names
`developer_manual_publication_v1`. Two answers to one question.

It is prior art and it is deliberate.
`SESSION_CLOSEOUT_MANUAL_POINTER_EVIDENCE_RECONCILIATION_2026-07-18.md` records
a pointer audit of **21 PASS, 1 REVIEW, 0 FAIL**, and names the one retained
REVIEW:

    "intentional MDO-350E controlled-publication versus active
     primary-reader role split"

The split is tracked, classified, and carried on purpose. **It is not a defect
and should not be filed as one.** What remains true and worth saying once: the
accepted MAN catalog was promoted 2026-05-27 and the reader pointer was decided
2026-06-03, so **the catalog is a correct record of a state that changed seven
days later, and nothing has re-run it since.** That is staleness with a date on
it, not a contradiction.

---

## 6. Recommendation

One action, already gated, already specified:

**Refresh the canonical harvest under the AIF-068 input contract.** That closes
the 34 and retires the three stale renames. It is the gate the contract names,
it needs no new tooling, and it does not touch prose.

Then, separately and afterwards, the 21 written-debt commands are a writing
task against a harvest that will by then be current. They are not urgent and
they are not blocked.

Do NOT re-point MANPUB, re-accept the catalog to chase the workspace drift, or
repair the 163 workspace links. All three would be work done against a
supporting workspace.

---

## 7. What this pass did NOT do

- No harvest refreshed, no page written, no pointer moved, nothing staged.
- **AIF-127 still NOT FIXED.**
- **No check that the 191 pages are ACCURATE.** Presence and absence only. A
  page can exist and be wrong, and nothing here would notice. AIF-114's finding
  -- published surfaces with no implementation -- is that failure mode in the
  other direction and it is live.
- No function surface measured. `SYSFUNC` holds 75 rows;
  `functions_and_expression_helpers.md` links 45.

---

## 8. Good Neighbour

    What changed      : this document. No code, no catalog, no publication, no
                        page, no pointer, no harvest.
    Whose area        : reports into AIF-068 (manualgen-harvest-feeder). The
                        publications, the harvest and the HELP store were READ
                        ONLY -- the HELP store belongs to a concurrent session
                        and was read by byte copy, never opened by the engine.
    What authorization: flush v5 Phase 6, "next, re-harvest debt", then "make
                        sure you have searched for prior art in this area".
    How to verify     : sha256 the primary reader artifact against
                        accepted_artifacts/primary_reader_artifact_v1.json; diff
                        harvested/HELP_COMMANDS.csv against
                        dottalkpp/data/help/COMMANDS.dbf on COMMAND.
    How to undo       : delete this file.
