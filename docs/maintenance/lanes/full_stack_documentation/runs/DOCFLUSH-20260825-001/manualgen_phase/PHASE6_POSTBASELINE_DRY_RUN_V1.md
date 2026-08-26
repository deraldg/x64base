# v6 Phase 6b -- the page generator was not blocked either, and it selects ONE key

    Run    : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Phase  : 6, R127 allow-list page generator. DRY RUN ONLY. Nothing written.
    Status : review-needed. PASS_CANDIDATE_ONLY once the expected key is declared.

## 1. Second time in one night, and the same correction

`PHASE6_DRY_RUN_AND_TWO_FINDINGS_V1.md` section 6 filed
`build_postbaseline_supported_command_pages.py` as owner-blocked on

    :391   if sys.version_info[:2] != (3, 12): raise SystemExit("Python 3.12.x is required")

The guard is real -- an EQUALITY, so 3.13 fails it too -- and the conclusion was
wrong for the second time tonight, for the same reason recorded in
`metacollect_phase/PHASE5_PREFLIGHT_AND_FINDING_V1.md` section 0. **The
interpreter is not the question; what the generator selects is.** The cloud
sandbox has 3.10, 3.11, 3.12 and 3.13 side by side.

What it took: three tarballs moved across (the script, `tools/manualgen/
manualgen_lib`, `tools/common` for `local_paths`), `PYTHONPATH` set, run under
`python3.12`. The device VM has only 3.10 and cannot reach `astral.sh` (403), so
the container was the route. **`--dry-run` writes nothing, so no output
directory was created on either side and no repository state moved.**

The general rule, stated once: **a version guard is a fact about an
INTERPRETER, not about a QUESTION.** So is "it is a Windows exe". Neither is a
reason to file an item as blocked while an interpreter or a compiler is one
command away.

## 2. What it selected

    --current-topics   harvest_candidate_v1/HELP_HELP_TOPIC.csv   (667 topics)
    --baseline-topics  harvested/HELP_HELP_TOPIC.csv              (665 topics)
    --help-lines       harvest_candidate_v1/HELP_HELP_LINE.csv
    --accepted-command-dir  published/developer_manual_publication_v1/
                            command_reference_v1/commands          (211 pages)
    --compose-catalog FOX --compose-catalog UI --compose-catalog DEV
    --reference-run   DOCFLUSH-20260825-001/harvest_20260826
    --dry-run

    DRY RUN -- selected 1 key(s), wrote nothing
      page key                     own  +comp   =src  incl
      DOT|BUILD                      3      0      3     3
    FINDING EXPECTED_KEY_MISMATCH:actual=DOT|BUILD:expected=
    status=FAIL

**That FAIL is the R127 guard working, not a defect.** The generator refuses to
proceed until the caller has NAMED in advance what it expects to be selected --
the whole point of an allow-list is that the tool VERIFIES rather than deduces
(`:104-108`). Re-run with the key declared:

    --expected-topic-key "DOT|BUILD"
    DRY RUN -- selected 1 key(s), wrote nothing
    status=PASS_CANDIDATE_ONLY

## 3. `pages=0` while one key was selected

Both runs print:

    postbaseline_supported_command_pages status=... pages=0 lineage=0

The counts report what was WRITTEN, and a dry run writes nothing, so they are
correctly zero -- and they sit one line below "selected 1 key(s)". A reader
skimming the summary line reads `pages=0` as "nothing selected". It is the same
legibility trap as every other number this lane has had to open tonight: a count
that is true about one question and read as the answer to another. Naming it
here rather than letting the next reader find it the hard way.

## 4. TWO topics were gained. Only ONE can ever be paged.

The store gained `DOT|BUILD` and `FOX|FILE` since the baseline harvest. Only
`DOT|BUILD` reached the selector, and the reason is one line:

    def supported(path):
        return {row["TOPICKEY"]: row for row in read_csv(path)
                if row.get("CATALOG", "").upper() == "DOT"          # <--
                and row.get("SUPPORTED", "").upper() in TRUE_VALUES}

**This generator is DOT-only by construction.** `FOX|FILE` is not skipped, not
deferred, and not reported -- it is outside the input set, so nothing mentions
it. Checked rather than assumed: there is no `file.md` in the 211 accepted
pages, and `FOX|FILE` is the ONLY topic named `FILE` in the store, so no slug
collision explains it.

Nor can composition rescue it. `--compose-catalog FOX` means a FOX topic's lines
JOIN a same-TOPIC DOT page (R127 2a). **`FOX|FILE` has no DOT sibling**, so its
lines have no page to join. Its content is in the store and unreachable from the
manual by either route.

Measured, with the strings printed rather than only the number -- supported
topics that are non-DOT and have no same-TOPIC DOT sibling:

    53 total     FOX 30     ED 23
    FOX: ! ALLTRIM ASC AT ATC CHR CTOD DATE DTOC FILE LEFT LEN LOWER LTRIM
         PADC PADL PADR PROPER REPLICATE RIGHT RTRIM SPACE STR STUFF SUBSTR
         TIME TRANSFORM TRIM UPPER VAL
    ED:  BUFFERING DECISION EDUCATIONAL_USE ENUM EXPRESSION FILTER GLOSSARY
         INTRO LOOPS METADATA MODEL NAVIGATION PREDICATE PROJECTION RELATION
         REL_ENUM SCRIPT SEARCH SEQUENTIAL STATE TABLE_RECORD_FIELD TESTING
         WORKAREA

**AND THE COUNT MUST NOT BE READ AS 53 MISSING PAGES.** Printing the strings is
what makes that visible: the FOX thirty are expression FUNCTIONS and the ED
twenty-three are teaching CONCEPTS, and this tool is named
`..._supported_command_pages`. Most of that 53 is plausibly out of scope by
design and only the owner of the manual can say so. What IS established is
narrower and is not a matter of taste: **one of the two topics v6 added to the
store cannot be reached by the phase whose job is to page new supported
topics, and the phase does not say so.** Silence is the defect, not the filter.

`build_complete_command_reference_index.py` does not close it either -- it
classifies pages that EXIST on disk into declared provenance layers
(`:106-113`); it does not select topics, so it cannot create what the page
generator never made.

## 5. Not prescribed

Whether FOX functions and ED concepts get pages, get a different generator, or
are correctly excluded is a ruling for the manual's owner. The runnable ask is
smaller: make the DOT-only filter REPORT what it drops, so a supported topic
leaving the phase silently becomes a line of output instead of an absence.

## Good Neighbor

    What changed  : one new document in this run's directory. NOTHING ELSE.
                    The dry run wrote no output directory; three read-only
                    tarballs were copied out of the tree and are gitignored
                    (`/tmp/` -- .gitignore:266).
    Whose area    : lane full_stack_documentation, run DOCFLUSH-20260825-001.
                    Section 4 concerns tools/manualgen -- reported, not edited.
    Authorization : the owner's standing instruction to run v6 to the end.
    Verify        : sed -n '/^def supported/,/^def /p' the generator -- expect
                      the CATALOG == "DOT" filter.
                    Re-run section 2's command with --expected-topic-key
                      "DOT\|BUILD"; expect PASS_CANDIDATE_ONLY, 1 key, 3 lines.
                    The 53: supported topics, CATALOG != DOT, TOPIC not among
                      any DOT topic's TOPIC, over HELP_HELP_TOPIC.csv.
    Undo          : delete this document. It asserts nothing the tools do not.

---

# 6. The version guard measured -- added 2026-08-26 at the owner's prompt

Section 1 treated `!= (3, 12)` as a real constraint that simply had to be routed
around. The owner's note -- *"in the sandbox, codex has had success with python
3.8 and 3.10"* -- is the better question: **is the guard true?**

Measured, with the guard neutralised in a COPY under `/tmp` and nothing in the
tree touched. One-line diff, `if False:` in place of the version test:

    python3.10   selected 1 key(s)  DOT\|BUILD  3 own  PASS_CANDIDATE_ONLY
    python3.11   selected 1 key(s)  DOT\|BUILD  3 own  PASS_CANDIDATE_ONLY
    python3.12   selected 1 key(s)  DOT\|BUILD  3 own  PASS_CANDIDATE_ONLY
    python3.13   selected 1 key(s)  DOT\|BUILD  3 own  PASS_CANDIDATE_ONLY

Byte-identical on all four. 3.8 was not present to run.

**The code contradicts its own guard.** All 35 files -- the generator,
`manualgen_lib`, `tools/common` -- open with `from __future__ import
annotations`, which is precisely the measure that makes `dict[str, dict[str,
str]]` and `str | None` legal on older interpreters: they become strings and are
never evaluated. Parsed with `ast.parse(..., feature_version=(3, 8))`, all 35
files are clean. Somebody wrote this to be portable and then pinned it to one
version.

**The real floor is 3.9, not 3.12**, and the reason is stdlib, not syntax:

    manualgen_lib/validation.py:58                   str.removesuffix   3.9+
    manualgen_lib/gate4_acceptance.py:150            str.removeprefix   3.9+
    manualgen_lib/publication_structure_candidate.py:61  str.removeprefix

So the owner's recollection lands almost exactly: **3.10 works and is now
proven; 3.8 is the one that would actually stop**, on three `removeprefix` /
`removesuffix` calls rather than on anything about types.

The guard is wrong in BOTH directions. `!=` refuses 3.13, which works, as
readily as 3.10, which works. `manualgen.py` already models the honest form --
its `PYTHON_312` check is a validation ROW that reports and lets the run
continue, which is how Phase 6a got a full inventory and dry run out of a 3.10
interpreter with one FAIL correctly recorded.

**NOT CHANGED HERE.** A version guard is a contract; loosening it is a ruling,
not a cleanup, and the one-line change belongs to whoever owns that promise:

    if sys.version_info[:2] != (3, 12):   ->   if sys.version_info < (3, 9):

**NOT CLAIMED:** that one dry-run invocation on one dataset proves the tool is
3.9-safe on every path. It exercised selection, composition and the R127
allow-list check; it did not exercise the write path, and a write path is where
a version difference would most plausibly bite.

**What the three ceilings share.** "It is a Windows exe" is a fact about a FILE.
"Requires Python 3.12" is a fact about an INTERPRETER. "Not buildable in the
mounted sandbox" was a fact about a sandbox that no longer existed. None is a
fact about the QUESTION, and none is a reason to file an item blocked while a
compiler or an interpreter is one command away. AIF-130's intake row now carries
all three.
