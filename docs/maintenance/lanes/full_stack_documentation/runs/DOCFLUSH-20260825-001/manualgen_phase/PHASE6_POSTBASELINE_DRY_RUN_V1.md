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
