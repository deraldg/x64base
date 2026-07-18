# Manualgen Section Delta Draft Contract v1

Status: active for per-target additive candidate generation.

## Purpose

Repackage the accepted 462-topic structural mapping into human-reviewable,
per-target additive packets without rewriting, replacing, or promoting any
existing manual section.

## Input chain

The generator consumes a passing structural reconciliation with all 462 topics
mapped, all 13 structural review topics resolved, zero remaining fallbacks, and
publication authority claimed as zero. It then reads the disposition run named
by that manifest and copies each approved Markdown topic block intact. It does
not re-read a different HELP/META snapshot or synthesize from ambient state.

## Required checks

- exactly 462 disposition topic blocks and 462 mapping rows;
- every mapping consumes exactly one topic block;
- no missing, duplicate, unused, or unmapped blocks;
- exactly 22 non-empty target packets;
- replacement, reader-pointer, and publication flags remain zero.

## Current proof

Run `MANRUN-20260717T234222Z-ECBB99AD` reports 462 approved, mapped, and used
topic blocks across 22 packets. Missing, duplicate, and unused counts are zero;
status is `PASS`.

The largest packets are Legacy and Compatibility Surfaces (185 topics),
Educational and Demo Commands (56), and Navigation, Browsing, and Search (32).
The smallest are Runtime Evidence (2), Command Surface (3), and the candidate
Partial HELP appendix (3).

## Boundary

Packets are evidence-bearing draft inputs, not finished prose or accepted
manual sections. The command does not mutate the primary body, either overlay,
the accepted appendices, MAN catalogs, HELP, metadata, reader pointers,
websites, or external publication.

The first risk-ordered prose batch now passes under
`MANUALGEN_PROSE_REVIEW_BATCH_CONTRACT_V1.md`. Human review of its three
anchored candidate files is the next gate; selective merge remains separately
authorized.
