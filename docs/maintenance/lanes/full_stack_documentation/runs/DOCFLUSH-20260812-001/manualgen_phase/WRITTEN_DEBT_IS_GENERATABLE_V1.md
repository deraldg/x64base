# The 21 written-debt commands are generatable, not authorial

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    Lane   : **AIF-068**. No new AIF.
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Status : **review-needed. MEASUREMENT ONLY -- nothing generated.**
             Generating command-reference prose from harvested rows is one of
             the input contract's separately authorized gates.

---

## 1. The headline, and the correction it makes

After the harvest promotion, Phase 6's remaining work was recorded as **"the 21
written-debt commands -- the only content work left"**, with the note that the
sections are AUTHORED rather than generated, so no re-harvest would write them.

That note is right about the SECTIONS and wrong about the PAGES.

**All 21 have HELP topics and HELP lines in the promoted harvest. 21 of 21.**

    command        topics  help lines      command        topics  help lines
    AVERAGE          2        6            NEXT             1       90
    BOOLEAN          2       47            PRIOR            1       66
    BROWSETUI        2       80            RBROWSE          1       41
    BROWSETV         3       47            REFRESH          2       78
    DISPLAY          2       88            REL_LIST         2        6
    ECHO             2       71            SIMPLEBROWSER    1      134
    FIRST            1       85            SMARTBROWSER     1      139
    FORMULA          3       71            SORT             1      161
    INDEXSEEK        2       94            TRANSFORM        1        3
    LAST             1       85            WHERECACHE       1      107
    LIST_LMDB        2      120

    topics present 21/21    zero help lines 0/21    median ~78 lines

The thinnest are `TRANSFORM` (3), `AVERAGE` (6) and `REL_LIST` (6); the rest
carry between 41 and 161 lines. **This is not twenty-one blank pages waiting for
an author.** It is twenty-one commands whose evidence has been sitting in the
store the whole time and never reached a page.

## 2. The renderer already exists, and eight pages were built this way

`tools/manualgen/build_postbaseline_supported_command_pages.py` --
*"Build candidate pages for supported commands added after a HELP baseline"* --
renders through `manualgen_lib.command_reference_candidate._render_page`, the
same renderer behind the accepted pages. It is what produced the **8
post-baseline coverage-repair pages** that `COMPLETE_COMMAND_REFERENCE_INDEX_V1.md`
declares as its third provenance layer (164 reader-linked + 19 supplemental + 8
repair = 191).

So the mechanism is proven, in this tree, on this manual.

## 3. BUT the selector will not pick these 21 up as it stands

`build()` selects:

    new_gaps = {key: row for key, row in current.items()
                if key not in baseline and slug_for(row["TOPIC"]) not in physical_slugs}

**Two conditions, and the 21 satisfy only the second.** They have no physical
page (condition two, satisfied). But they are not new since the baseline --
they were in the 2026-05-14 store, eleven days before the section files were
written, which is exactly why they were classed as *never harvested* rather than
*arrived since*. `key not in baseline` excludes them.

The tool is correctly scoped to what its name says: **commands added AFTER a
baseline.** These are commands that predate the baseline and were skipped. Same
missing page, different reason, and the selector distinguishes them.

**Two ways to close that, and the choice is a maintainer's:**

  (a) **Pass a narrower `--baseline-topics`** -- a topic set that legitimately
      excludes these 21 -- so the existing selector picks them up with no code
      change. Cheapest, but it means constructing a baseline to obtain a result,
      which is the kind of move that should be visible in the run record rather
      than buried in an argument.
  (b) **Add a second selector** for "supported topic, no physical page,
      regardless of baseline". Honest about what it is, and it is a code change
      to `tools/manualgen/`.

(b) reads truer. (a) is faster. Neither was done here.

## 4. Why nothing was generated

The harvest input contract's authority boundary lists, verbatim:

    generating or accepting command-reference prose from harvested rows

as a **separately authorized gate**, alongside replacing `harvested/` and moving
accepted pointers. Replacing the harvest was authorized this afternoon and done.
**Generating prose was not, and generating into a scratch directory is still
generating.** So this document stops at the measurement.

## 5. What this changes about the remaining work

    BEFORE   "21 commands need prose written" -- an authoring task, open-ended,
             requiring house voice, evidence rules and review of every page.

    AFTER    21 commands have evidence and no page. The renderer exists and has
             produced 8 pages this way already. What is missing is a selector
             that admits pre-baseline gaps, and the authorization to run it.

**That is a smaller and much better-defined piece of work than the open list
implied**, and it is the difference between "write the manual" and "run the
generator that writes it, then review 21 candidates."

**What it does NOT become:** automatic. `_render_page` output is a CANDIDATE.
The tool's own success status is `PASS_CANDIDATE_ONLY`, the index tracks the 8
repair pages as their own provenance layer rather than folding them in, and
every page still wants a read before it is reader-linked from a section.

## 6. What was NOT done

- **Nothing generated.** No page written, no candidate directory created, no
  tool run.
- No selector changed, no baseline constructed.
- The 25 accepted sections and their hashes are untouched, and none of the 21 is
  linked from any section list -- linking them is a further step beyond page
  generation.

## 7. Good Neighbour

    What changed      : this document. Nothing else.
    Whose area        : reports into AIF-068. `tools/manualgen/` was READ, not
                        modified or run. The promoted harvest was read.
    What authorization: flush v5 Phase 6, "next". Explicitly NOT the contract's
                        prose-generation gate, which is why this stops at
                        measurement.
    How to verify     : join the 21 names against
                        `harvested/HELP_HELP_TOPIC.csv` on TOPIC and count
                        matching rows in `harvested/HELP_HELP_LINE.csv`; 21 of
                        21 return a topic and a nonzero line count.
    How to undo       : delete this file.
