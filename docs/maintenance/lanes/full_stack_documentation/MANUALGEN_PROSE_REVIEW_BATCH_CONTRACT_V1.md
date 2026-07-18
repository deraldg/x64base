# Manualgen Prose Review Batch Contract v1

Status: active for risk-ordered human prose review.

## Purpose

Convert selected additive topic packets into anchored, human-readable prose
candidates without editing an accepted section, appendix, reader pointer, or
publication surface.

This gate begins with the three smallest packets so the review vocabulary and
merge controls are proven before larger command families enter prose drafting:

- Runtime Evidence: `DOT|REGRESSION` and `DOT|TEST`;
- Command Surface: `DOT|GENERIC`, `UI|ARCTICTALK`, and `UI|FOXPRO`;
- Partial HELP appendix: `DOT|CANARY`, `FOX|DO`, and `FOX|RUN`.

## Input chain

The generator consumes the latest passing 462-topic, 22-packet section-delta
manifest. It selects exactly the three named packets, verifies each packet
against the SHA-256 stored by that manifest, and requires the exact eight-topic
policy set. It also hashes the two existing primary section targets and checks
that every proposed insertion heading occurs exactly once.

## Review dispositions

| Disposition | Meaning |
| --- | --- |
| `ADDITIVE_PROSE` | Evidence supports a bounded explanatory addition with availability and side-effect caveats. |
| `CANARY_CROSS_REFERENCE` | Preserve an identity for dispatch/metadata audit without polishing it into normal user workflow prose. |
| `APPENDIX_ONLY` | Keep partial or legacy syntax segregated from supported-command prose. |

The initial policy assigns four topics to additive prose, one to canary
cross-reference, and three to appendix-only treatment.

## Required checks

- exactly eight policy topics and eight selected input topics;
- every selected topic occurs exactly once;
- no missing, unexpected, or duplicate topic identity;
- all three packet hashes match the upstream manifest;
- every primary-section anchor exists exactly once;
- exactly three candidate prose files;
- canonical-section, accepted-appendix, reader-pointer, publication, and
  HELP/metadata mutation flags remain zero.

## Current proof

The originally reviewed run `MANRUN-20260718T012220Z-6CF3FC93` passed all
required checks. After newline-only byte drift was detected by the next gate,
normalized text comparison passed 3/3 and the same prose was regenerated as
`MANRUN-20260718T020630Z-9367A5BA`. The hash-reconciled run emits the
topic disposition ledger, three anchored candidate prose files, and the
hash-bound batch manifest beneath
`docs/manuals/developer/manualgen/generated/manualgen_prose_review_batches/`.

## Boundary

The generated text is editorial draft material. Suggested anchors are merge
coordinates, not merge authority. The batch does not edit either referenced
primary section, create an accepted appendix, rebuild the combined reader,
change a pointer, or publish externally.

Human review approved a non-published selective merge candidate. That gate now
passes under `MANUALGEN_SELECTIVE_MERGE_CANDIDATE_CONTRACT_V1.md`. Canonical
acceptance must still re-check the recorded target hashes and must not silently
broaden partial HELP or canary topics into supported-command claims.
