# Manualgen selective-merge context decision

Decision: approved for canonical acceptance preflight.  
Recorded: 2026-07-18 UTC.  
Selective merge: `MANRUN-20260718T020658Z-BFE7F605`.  
Canonical mutation authorized: no.  
Publication authorized: no.

## Decision

The contextual reader, two copied sections, candidate appendix, and three diffs
are suitable inputs to a canonical acceptance preflight. This decision approves
the content and placement for planning; it does not accept any section, append
the appendix, replace the primary reader, update accepted evidence, or publish.

## Reviewed content

| Topics | Context result | Evidence result |
| --- | --- | --- |
| `REGRESSION`, `TEST` | PASS | Current usage contracts support launcher syntax, delegated execution, logging, continuation/comment handling, processed/error counts, and non-read-only classification. |
| `GENERIC` | PASS | DOTREF retains the developer placeholder identity; source implements a build-conditioned developer workbench. The candidate conservatively keeps normal workflow claims canary-level. |
| `ARCTICTALK`, `FOXPRO` | PASS | DOTREF and conditional shell registration support the bare launch entries; source confirms Turbo Vision build conditioning and `FOXTALK` as the legacy ArcticTalk alias. |
| `CANARY` | PASS AS PARTIAL | Runtime registration maps `CANARY` to the catalog-canary handler, while curated DOTREF support remains absent. Segregation in the partial appendix is appropriate. |
| FOX `DO`, FOX `RUN` | PASS AS LEGACY/UNSUPPORTED | FOXREF preserves their exact legacy forms with `supported=false`; the appendix does not infer current implementation. |

## Structural checks

- base primary reader hash:
  `08343C235D447C57EF4A270F2580339B4933401D16C1603A612785025DDDAC95`;
- two copied-section diffs: 55 additions, 0 deletions;
- combined-reader diff: 106 additions, 0 deletions;
- each new heading occurs exactly once in the contextual reader;
- partial appendix occurs once and remains visibly non-authoritative;
- candidate manifest: `PASS`, 8 topics, 0 hash failures, 0 anchor failures,
  0 extraction failures, 0 canonical hash changes;
- publication authority claimed: `0`.

The primary reader's inherited section-marker asymmetry is unchanged at 24
begin markers and 13 end markers. This review does not treat pre-existing
marker debt as a new selective-merge defect.

## Next gate

Run the canonical acceptance preflight against the active primary reader and
its accepted evidence records. Do not copy the contextual reader verbatim: its
candidate-only banner and provenance comments must not become publication text.
