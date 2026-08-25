# Phase 6 -- the re-harvest debt, measured

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Method : read-only. Live HELP command registry against the accepted
             publication's section files, appendices, assembled body and
             command-reference pages. No engine, no build, no mutation.
    Status : **review-needed.** One item needs a maintainer decision (D1).

---

## 1. Headline

**The accepted publication has 163 command links and every one of them is
broken. All 163 resolve against a SIBLING publication directory that the
catalog did not accept.**

Underneath that wiring fault the content is in better shape than the v4 estimate
said: **47 of 320 commands (14.7%) are absent from the manual entirely**, and
**nothing in the manual documents a command that no longer exists** -- zero
stale pages out of 191. The manual has aged by omission only.

---

## 2. The two publications, and which one was accepted

`MANPUB` names four artifacts. Two matter here:

    MANPUB-001  active_publication                  .../developer_manual_publication_v1_media_section_v1
    MANPUB-004  original_publication_v1_preserved   .../developer_manual_publication_v1

The **active** publication holds the 24 section files and the appendices.
The **preserved** publication holds `command_reference_v1/` -- 191 command
pages and a provenance index.

The section files link their commands as `../../command_reference_v1/commands/<slug>.md`.
Resolved from the active publication that path does not exist:

    command links in the active publication's section files   163
    resolve from the ACTIVE publication (MANPUB-001)            0     <- 163 broken
    resolve from the PRESERVED publication (MANPUB-004)       163     <- all of them

**This is not a content gap and should not be repaired as one.** The pages
exist, they are current, and they are one directory away. What went wrong is
that the publication replacement recorded by MDO-242 moved the reader-facing
body and left the command reference behind, and no gate compared the two.

The dates say the split widened afterwards rather than healing:

    section files (active publication)   2026-05-25 21:38
    catalog promoted                     2026-05-27 14:47
    command pages (preserved)            2026-07-18 .. 2026-07-28

**The command reference was rebuilt two months AFTER the catalog was accepted,
in the publication the catalog did not accept.** The accepted baseline has
therefore never pointed at the current command reference at any moment in its
life.

---

## 3. The command surface today

Read from the live HELP store `dottalkpp/data/help/COMMANDS.dbf`
(dBase III, generated 2026-08-25, the AIF-126 rebuild):

    460 catalog rows   320 distinct command names
    DOT 256   FOX 175   ED 29    (a name may appear in more than one catalog)

`IMPLEMENT` separates: 409 rows true, 51 false. `SUPPORTED` does not -- 456 of
460 are true, which is the FINDING_STATUS_SUPPORTED_SEPARATES_NOTHING shape, so
it was not used as a filter here.

---

## 4. Coverage, in three tiers

A command counts as covered by the strongest evidence available, not by a single
proxy. Three tiers, measured separately because they answer different questions:

    TIER 1  has a reference page, or is linked from a section list     193
    TIER 2  named in the manual body, but no reference page             80
    TIER 3  ABSENT -- no page, no link, name never appears at all       47
                                                                      ---
                                                                       320

**TIER 2 is mostly not debt.** It is dominated by SET-family variants and
aliases (`SET CASE`/`SETCASE`, `SET ORDER`/`SETORDER`, `ERROR CLEAR`/
`ERROR_CLEAR`, ...), which the manual handles deliberately in
`appendices/review_and_deferred_set_family.md` and
`review_and_deferred_alias_and_variant_review.md`. Counting an alias as an
undocumented command would have inflated the debt by roughly seventy percent.
That is precisely the trap: **page-existence alone is a proxy that cannot answer
"is this documented", and using it as one would have produced a confident wrong
number.** The first cut of this measurement said 114. It was wrong.

---

## 5. TIER 3 -- the actual debt: 47 commands

45 of 47 are NATIVE (`DOT`). Only `TRANSFORM` (FOX-only) and `SEARCH` (ED-only)
are not. 46 of 47 are `IMPLEMENT`ed -- `SEARCH` is the single unimplemented one
and is correctly omitted.

Split by whether the command existed when the manual was written. Baseline is
the tracked legacy store `dottalkpp/data/dbf/help/commands.dbf`, generated
2026-05-14, eleven days before the section files:

### 5a. NEVER HARVESTED -- available all along, still absent (23)

    AVERAGE      BOOLEAN      BROWSETUI    BROWSETV     DISPLAY
    ECHO         FIRST        FORMULA      INDEXSEEK    LAST
    LIST_LMDB    NEXT         PRIOR        RBROWSE      REFRESH
    REL_LIST     SEARCH       SHOW         SIMPLEBROWSER
    SMARTBROWSER SORT         TRANSFORM    WHERECACHE

These are not a staleness problem. They were in the store the generator read
and did not come out the other side. `DISPLAY` and `SORT` are ordinary dBase
verbs; `FIRST`/`LAST`/`NEXT`/`PRIOR` are a complete navigation quartet the
Navigation section documents the other half of (`GO`, `SKIP`, `TOP`, `BOTTOM`).
**A gap with that shape is worth understanding before it is filled** -- four
sibling verbs going missing together looks like a generator boundary, not
twenty-three independent oversights.

### 5b. ARRIVED SINCE -- genuine re-harvest (24)

    APPGUI    ARCTICTALK  BBOX       BBS        BUILD INFO  DDICT
    EVALDIFF  EXIT        EXITS      EXPORTFUNCTIONS
    GUI       HANUKKAH    MAINT      MANSTAR    MANUAL      MSGMGR
    NET       REGRESSION  SET CDX    SET CNX    SET LMDB    SET NEAR
    SMTP      STRCAT

The surface moved **+35 names / -4 names** between 2026-05-14 and 2026-08-25.
Three of the four losses are renames the manual never saw either
(`SETNEAR`->`SET NEAR`, `SIMPLEBROWSE`->`SIMPLEBROWSER`,
`SMARTBROWSE`->`SMARTBROWSER`); only `VUSE` actually left.

### 5c. Two measurement caveats, stated rather than buried

`DISPLAY` and `MANUAL` appear 52 and 325 times in the manual body as ordinary
English words. The classification is by the command name as a standalone
all-caps token plus page and link presence, so both are correctly TIER 3 -- but
a case-insensitive word search would say otherwise and someone will run one.
Neither has a reference page and neither is named as a command anywhere.

---

## 6. The v4 claim was half wrong, and this corrects it

Flush v4 recorded the candidate as lacking **BBS / NET / CANARY / CMDREL /
FORMULA / EDIT**. Measured:

    BBS      absent      arrived after 2026-05-14
    NET      absent      arrived after 2026-05-14
    FORMULA  absent      present since 2026-05-14, never harvested
    CANARY   HAS A PAGE  commands/canary.md   (2026-07-28)
    CMDREL   HAS A PAGE  commands/cmdrel.md   (2026-07-28)
    EDIT     HAS A PAGE  commands/edit.md     (2026-07-28)

Three of the six were repaired by the July command-reference rebuild. **The
claim was not re-measured after that rebuild, so it carried three false
negatives for a month.** The reason it went unnoticed is section 2: the pages
landed in the publication the catalog does not point at, so nothing that reads
the accepted baseline could see them.

---

## 7. What the 191 pages are, and that nothing is stale

`COMPLETE_COMMAND_REFERENCE_INDEX_V1.md` declares its own provenance layers and
the count reconciles exactly:

    reader-linked            164
    supplemental standalone   19
    post-baseline repair       8
                             ---
                             191     status: supported 187 / partial 3 / pending 1

163 of the 164 reader-linked pages are linked from the 11 section files that
carry command lists; the 164th is `REL ENUM`, linked from elsewhere. The other
13 sections are prose and carry no list.

**Zero of the 191 pages document a command name that is not in the surface
today.** The manual contains nothing wrong. It is only missing things.

---

## 8. D1 -- DECISION NEEDED

The re-harvest is cheap only if the wiring is settled first, and the wiring
question is the same one as S5 in the catalog verification: **which publication
is the manual?**

  (a) The active publication (MANPUB-001) is the manual -> bring
      `command_reference_v1/` into it, then re-accept. The 163 links go from
      0/163 to 163/163 with no prose written. **This changes the debt count by
      nothing -- it stays at 47** -- and that is the point: it fixes no content,
      it makes content fixable. Nothing written before it is visible from the
      accepted baseline.
  (b) The preserved publication (MANPUB-004) is the manual -> re-point MANPUB
      and re-run the catalog against it.

Doing the 47-command harvest before (a) or (b) writes pages into a directory
that half the tooling does not read. **Order matters here and it is the whole
recommendation.**

After that, the content work is 24 arrived-since commands (a normal re-harvest)
and 23 never-harvested ones (which want a look at WHY the generator skipped
them, starting with the FIRST/LAST/NEXT/PRIOR quartet, before anyone writes 23
pages by hand).

---

## 9. What this pass did NOT do

- No page written, no link repaired, no catalog re-accepted, nothing staged.
- **AIF-127 still NOT FIXED.**
- No check that the 191 existing pages are ACCURATE. This measured presence and
  absence, not correctness. A page can exist and be wrong, and nothing here
  would notice.
- No function surface measured. `SYSFUNC` holds 75 rows and
  `functions_and_expression_helpers.md` links 45; that is a separate count and
  was not taken.

---

## 10. Good Neighbour

    What changed      : one new document (this file). No code, no catalog, no
                        publication, no page, no link.
    Whose area        : full_stack_documentation lane (mine). manualgen's
                        publications and the HELP store were READ ONLY -- the
                        HELP store belongs to a concurrent session and was read
                        by byte copy, not opened by the engine.
    What authorization: flush v5 Phase 6, "next, re-harvest debt".
    How to verify     : re-run the three tiers from
                        dottalkpp/data/help/COMMANDS.dbf against the section
                        files, appendices, assembled body and
                        command_reference_v1/commands/. The link count is
                        reproducible with any markdown link extractor.
    How to undo       : delete this file.
