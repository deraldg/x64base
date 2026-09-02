# Should the acceptance chain merge per flush iteration?

    run       : DOCFLUSH-20260901-002 (v8)
    question  : owner, 2026-09-02 -- "fix the acceptance chain for the merge to
                work per flush iteration or if not necessary why"
    answer    : **NOT NECESSARY, AND THE FIX WOULD BE THE WRONG REPAIR.**
                The thing that actually blocked per-iteration flow was
                `build-disposition-candidate`, and that is now fixed.

## The short answer

There are TWO paths by which content reaches the developer manual. They have
different cadences on purpose.

    PATH 1  GENERATED REFERENCE          per flush iteration
            harvest -> build-reference-candidate
                    -> build-command-reference-candidate
                    -> build-command-reference-review-book
            This is how NEW HELP CONTENT reaches the manual. It scales with the
            store: 666 topics, 29700 lines, regenerated from the harvest every
            run.

    PATH 2  CURATED PROSE                per approved review batch
            prose review -> selective merge -> controlled acceptance
            This inserts HUMAN-WRITTEN NARRATIVE at three named anchors in the
            accepted reader. It is per-approval by design and does not track the
            store at all.

**The controlled-acceptance chain is Path 2.** It is a prose applier, not a
content pipeline. Making it iterate per flush would not carry a single extra
HELP topic into the manual, because it does not carry HELP topics -- Path 1
does.

## Why it CANNOT be generalized without rewriting it

The blocker is not the hardcoded counts. It is the code structure, and the
counts are a consistency assertion ON that structure.

`controlled_acceptance.py` indexes three literal constants directly:

    246   planned_sections[slug] = rebuilt
    248   appendix_row = merge_by_target[PARTIAL_HELP_SLUG]
    303   (runtime_output, planned_sections[RUNTIME_SLUG]),
    304   (command_output, planned_sections[COMMAND_SLUG]),
    370   (runtime_output, merge_by_target[RUNTIME_SLUG]["base_path"], "replace"),
    371   (command_output, merge_by_target[COMMAND_SLUG]["base_path"], "replace"),

    RUNTIME_SLUG       = "runtime_evidence_source_verification_and_canary_closure"
    COMMAND_SLUG       = "command_surface_dispatch_and_entry_variants"
    PARTIAL_HELP_SLUG  = "partial_help_reference"

Direct dict indexing by named constant, not iteration over whatever the
candidate contains. So:

    expected_counts  sections=2, appendices=1, diffs=3
                     maps EXACTLY onto those three slots.

Relaxing `expected_counts` alone would make things worse, not better: a
candidate missing `PARTIAL_HELP_SLUG` would `KeyError` at line 248 instead of
failing a readable check, and a fourth fragment would be **silently ignored**
rather than refused. The counts are the guard that keeps that from happening.

The merge semantics are hardcoded in the contract too, not just the code
(`MANUALGEN_SELECTIVE_MERGE_CANDIDATE_CONTRACT_V1.md`): the Runtime Evidence
fragment inserted once after the smoke/shakedown/regression subsection, the
GENERIC canary note once after Command Surface, the UI-entry note once after
Aliases and Entry Variants, the Partial HELP prose as a separate appendix. Four
named insertions at four named places. That is a specification of one merge, not
of a merge engine.

## Why per-batch is the RIGHT cadence for Path 2

From the same contract:

> The generator requires a durable review decision naming the exact passing
> prose-review manifest. Approval extends only to generated candidates.

Prose is human narrative. It changes when someone writes new narrative, which is
not "every time the HELP store is rebuilt". Tying it to the flush cadence would
mean either re-applying identical prose every run (which is what the
`PARTIAL_HELP_ALREADY_IN_AGGREGATE` guard exists to stop) or inventing prose to
justify the run.

The idempotence guard firing this session is the system working. It caught a
replay of the 2026-07-18 acceptance to the second.

## What ACTUALLY blocked per-iteration flow, and is now fixed

Path 1 is the per-iteration path, and it was blocked -- but not by the
acceptance chain.

    command_reference_candidate.py:226
        if reference.get("transform_status") != "PASS"
           or disposition.get("status") != "PASS":
            <refuse>

**Path 1 requires BOTH the reference candidate AND the disposition candidate to
PASS.** At the start of this session:

    build-reference-candidate    blocked by PYTHON_312 (returned created=0)
    build-disposition-candidate  FAIL (missing_policy=1, extra_policy=13)

Both are now green:

    build-reference-candidate    PASS  666 topics, 29700/29700 lines,
                                 unclassified 0, command_without_topic 0
    build-disposition-candidate  PASS  missing 0, extra 0, invalid_targets 0

So the repair that makes the flush iterate was the disposition policy repair,
not an acceptance-chain rewrite. **Path 1 is open now and was not before.**

## The one thing that WILL need attention each iteration

`REVIEW_DISPOSITIONS` is a hand-maintained table and it drifted against the
store between July and September -- 13 entries naming topics that had moved on,
one topic with no policy. It will drift again every time the store grows.

That is the same shape as `collect_set_subcommands()` in the reflection surface
and the old `is_expression_function_name()` list in CMDHELP: **a hand-kept list
standing where a derivation belongs.** It is the standing per-iteration cost of
this design, and the durable fix is to derive dispositions from the contracts
rather than maintain a parallel table -- the same move the owner already ruled
for dotref (`dotref_autogen.py`).

That is a real lane and it is not this run's.

## Recommendation

1. **Do not modify the acceptance chain.** It is correctly scoped, correctly
   guarded, and its refusal this session was accurate.
2. **Use Path 1 for content.** It is unblocked and it is what carries the 193
   new topics.
3. **Run Path 2 only when there is new approved prose**, with a review decision
   naming that batch -- which is what the contract already says.
4. **Charter the disposition-derivation lane** if the per-iteration drift cost
   is judged too high. That is the only change here that would reduce recurring
   work, and it targets the policy table, not the applier.
