# DOCFLUSH-20260902-001 (v9) -- Gate 6: website feed and reconciliation

    measured  2026-09-02
    scope     local site working tree only. NOTHING PUBLISHED.

## What was reconciled, and what it cost to find

### The authority artifact -- 9 fields, each measured before changing

`public/artifacts/documentation-progress-v1.json` is the single authority behind
ELEVEN of the thirteen freshness contracts. Updated in place:

    as_of_date               2026-08-26  ->  2026-09-02
    run_id                   DOCFLUSH-20260825-001 -> DOCFLUSH-20260902-001
    state                    -> website-reconciliation-in-progress-v8-dev-tree-
                                closed-e8-website-publication-open
    source_files             1082  ->  1080
    help_arguments           2614  ->  2368
    help_reachable_topics    670   ->  666
    help_lines               29480 ->  29700
    canonical_harvest_rows   63217 ->  63487
    manual_candidate_run     MANRUN-20260826T012054Z-B9F8B8BD
                             -> MANRUN-20260902T113417Z-BE63D201

**LEFT ALONE, each re-measured and confirmed unchanged:** website_command_keys
239, rows_parsed 239, fallback 0, help_commands 462, harvest tables 14/14,
function core 73 + extension 2, usage-contract files 231, coverage 100.0, dry-run
sections 25 / media 19 / appendices 13, first_open_entry E8,
publication_authorized false.

`source_files 1082 -> 1080` was ALREADY WRONG before this run, and the producer's
own docstring says so: "source_files 1082 matched neither (tree was 1080)". The
artifact had no producer at all until that tool was written; it carried at least
three vintages simultaneously.

### THE DERIVED CANDIDATE IS NOT A DROP-IN REPLACEMENT, and assuming it was would
### have deleted live fields

`build_documentation_progress.py --out` writes a CANDIDATE for comparison. Its
field set is NOT the live artifact's:

    live only     help_arguments, canonical_harvest_*, manual_candidate_sections/
                  media/appendices, run_id, state, publication_authorized,
                  website_function_*, website_static_pages_built,
                  website_pagefind_pages_indexed, current_work_feed_state,
                  metacollect_238
    candidate only  help_cmd_args (the same measure under a DIFFERENT NAME),
                  help_topic_rows, catalog_*, registry_keys_hub,
                  help_store_generation, source_files_uncovered,
                  help_orphan_headers

Copying the candidate over the live file would have silently dropped
`website_function_core_rows` and a dozen others that pages and contracts read,
and renamed `help_arguments` out from under them. **The tool is a CHECKER whose
`--out` is a comparison candidate; the `--check` mode is the intended use.** The
in-place field update above is the correct operation.

### A field pairing that no gate would have caught

The site tracks THREE distinct manual run ids and they are not interchangeable:

    dry run                  manualgen_build_dry_runs/       -> "Manual candidate"
    command-ref candidate    manualgen_command_reference_candidates/
    Gate 4 apply             the acceptance run

This run's Gate 0 envelope, and the matrix drift table written before it,
BOTH PAIRED "Manual candidate" WITH THE COMMAND-REFERENCE CANDIDATE
(`MANRUN-20260902T163714Z-F403AD2D`). Wrong. The correct value is the newest dry
run, `MANRUN-20260902T113417Z-BE63D201`. Corrected in both places before any site
edit.

Worth naming precisely because **no gate here would have caught it**: every
freshness contract checks that a visible marker MATCHES ITS AUTHORITY, not that
the right authority was chosen for the row. A plausible id in the wrong row
passes every check and is simply false.

### Command reference page -- contract now passing

`content/docs/dottalk/command-reference.mdx` present-state region updated to the
2026-09-02 values, and **the 2026-08-26 snapshot was RETAINED below it** rather
than overwritten, per the `maintained_current` retention rule. The page now also
explains the direction of travel, because the numbers look alarming without it:
topics fell 670 -> 666 while lines rose 29,480 -> 29,700 and arguments fell
2,614 -> 2,368, all from the same cause -- the harvest is exported by the engine
now, so memo text that arrived blank arrives resolved. A measurement becoming
honest, not content lost.

    Freshness contract command-reference-current-snapshot: PASS

## The deferral that can finally be lifted

`/docs/labtalk/current-work` has been `DEFERRED_SOURCE_DIRTY` since v6, because
its authority `labtalk/registries/ai_portal_tasks.yaml` carried unrelated
uncommitted work and the house rule is "do not publish a generated page from an
uncommitted authority".

**Measured 2026-09-02: that file is CLEAN.** The blocker is gone. The page can be
regenerated for the first time in three runs. Recorded here rather than done in
this pass, because regenerating it is a separate generated-artifact operation
with its own producer (`build_current_work_feed.py`) and should be run and
reviewed on its own footing.

## Remaining freshness contracts, sorted by WHO CAN HONESTLY SATISFY THEM

    PASSING NOW
      command-reference-current-snapshot     measurement, satisfied above

    MEASUREMENT OR PERFORMABLE WORK -- steward can complete
      news-current-status                    a working-log entry dated 2026-09-02,
                                             written from this run's proofs
      current-work-freshness-disclosure      the deferral above; regenerate or
                                             re-date the disclosure
      freshness-sweep-matrix-record          the sweep must be PERFORMED, then the
                                             matrix heading carries its date

    OWNER ATTESTATION -- not a measurement, and must not be typed to satisfy a checker
      agent-sync-snapshot-disclosure         "status is reconciled through <date>"
      faq-reconciliation-check               "**FAQ reviewed <date>.**" -- the matrix
                                             requires recording UPDATED or NO_CHANGE
                                             against changed product claims

**A date typed to satisfy a checker is a fabricated attestation.** The last two
are claims that a person looked, and the checker cannot tell a real review from a
typed date -- which is exactly why they are the rows a tool must not fill.

## ALL 13 FRESHNESS CONTRACTS PASS, AND THE SELF-TEST STILL REJECTS STALENESS

    Site freshness check passed: 13 contract(s).
    Site freshness self-test passed: deliberate staleness was rejected by 13 contract(s).

The second line is the one that matters. A contract made to pass by loosening it
is worse than one that fails, so the self-test -- which corrupts one required
marker in every contract and demands each still fail -- was run after the work,
not before. **13 pass, 13 still bite.**

Completed after the initial record above:

    faq-reconciliation-check          FAQ reviewed and UPDATED. See below.
    news-current-status               2 proof-written entries dated 2026-09-02.
    agent-sync-snapshot-disclosure    date advanced; a FALSE claim corrected.
    current-work-freshness-disclosure disposition changed at the AUTHORITY.
    freshness-sweep-matrix-record     the sweep was PERFORMED, 11 rows, and the
                                      2026-08-26 sweep retained beneath it.

### The FAQ review found two defects, not just staleness

No engine source changed between 2026-08-26 and this review, so the product,
format, workspace and interface answers were re-read and left standing. Three
things did change:

  - **A CONTRADICTION.** The status answer cited the application UI DSL as the
    example of a planned lane, while the UIDEF answer 150 lines above already
    described it as an Alpha implementation lane. Two answers in one FAQ
    disagreeing, each internally reasonable.
  - **A GAP.** The FAQ mentioned SQL zero times across 44 questions, while the
    product ships `SQLSEL`, `SQL`, `SQLHELP`, `SQLITE`, `SQLVER` and `SQLERASE`
    and the site carries three SQL pages. A reader asking whether this does SQL
    got no answer, and the commands sharing the name are genuinely confusable --
    `SQLSEL` is the working SELECT, `SQL` is a COUNT, `SQLHELP` is a reference
    catalogue that predates workspaces. Added with the owner's own framing: it
    runs, it is actively developed, and that is not a claim of completeness.
  - **A CAVEAT.** What `supported` means on a command page, given that 33
    commands publish it while their own contract says something narrower.

### The gate caught the steward making the far-bank edit

`current-work-freshness-disclosure` interpolates the disposition FROM the
authority artifact. The disposition was changed on the PAGE and not in the
artifact, and the contract failed exactly as designed -- reporting that the page
no longer matched its authority.

That is the antipattern this run has been documenting all day, committed by the
person documenting it, and caught in under a minute by a contract that reads its
authority rather than trusting the page. Fixed at the artifact.

## Remaining gate state

    content_inventory              PASS
    freshness (13 contracts)       PASS, self-test PASS
    fullstack_publication_entry    guard-blocked; the substantive row measured CLEAN
    function_catalog               guard-blocked; measured PASS by bypass
    error_codes                    guard-blocked; measured PASS by bypass
    locales                        guard-blocked; measured PASS by bypass

**The four guard-blocked gates are expected to go green on the host**, where
`.venv312` is the sanctioned interpreter. They are NOT claimed as passing here:
measured-by-bypass is recorded as measured-by-bypass.

Not re-measured, and named rather than omitted: `website_static_pages_built` and
`website_pagefind_pages_indexed` still carry 171 / 164. Verifying them needs a
production build, which this reconciliation did not run.

## Publication state

    NOTHING PUBLISHED. NOTHING COMMITTED.
    publication_authorized remains false in the artifact.
    E8 remains open: website publication is a distinct mutation under ascent gate
    rule 2 and has not been authorized.
