# Manualgen Selective Merge Candidate Contract v1

Status: active for non-published contextual review assembly.

## Purpose

Apply a human-approved prose-review batch to copied manual inputs and build a
full contextual reader candidate without mutating any canonical or accepted
manual surface.

## Required authority

The generator requires a durable review decision naming the exact passing
prose-review manifest. Approval extends only to generated candidates. It does
not imply section acceptance, appendix acceptance, reader replacement, pointer
movement, or publication.

## Merge semantics

- An anchor of the form `## Heading` means insert after that heading's complete
  subsection body and before the next level-two heading.
- The Runtime Evidence fragment is inserted once after the complete smoke,
  shakedown, regression, build, and release subsection.
- The `GENERIC` canary note is inserted once after the complete Command Surface
  subsection.
- The conditional UI-entry note is inserted once after the complete Aliases
  and Entry Variants subsection.
- The Partial HELP prose becomes a separate candidate appendix and is appended
  only to the generated contextual reader.
- Reviewed prose may not be silently expanded or reclassified during the
  mechanical merge.

## Required outputs

- two copied, selectively merged section candidates;
- one candidate Partial HELP appendix;
- one full non-published reader candidate based on the current primary reader;
- unified diffs for both sections and the reader;
- a merge ledger, contextual-review report, and hash-bound manifest.

## Required checks

- the review decision names the selected prose run;
- the prose manifest and all three prose files match their recorded hashes;
- both canonical target hashes still match the prose manifest;
- the primary reader exists and is bound by hash;
- each insertion anchor and prose extraction marker occurs exactly once;
- section diffs are additive only;
- two section candidates, one appendix, one reader, and three diffs are emitted;
- canonical section hashes remain unchanged after generation;
- canonical manual, accepted appendix, reader pointer, publication, HELP, and
  metadata mutation flags remain zero.

## Boundary

All outputs live beneath
`generated/manualgen_selective_merge_candidates/<run-id>/`. They are review
artifacts, not an accepted manual workspace. Any later canonical merge requires
a separate authorization and a fresh hash preflight.

## Current proof

Run `MANRUN-20260718T020658Z-BFE7F605` passes with eight reviewed topics, two
copied section candidates, one candidate appendix, one full reader candidate,
and three unified diffs. The section candidates add 33 and 22 lines with zero
deletions. Hash, extraction, anchor, and canonical-change findings are zero.
