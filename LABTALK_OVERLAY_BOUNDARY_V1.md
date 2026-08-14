# LabTalk Overlay Boundary v1

LabTalk is an optional educational/publication layer over DotTalk++ and x64base. It must not become a hard dependency of the core engine.

## Boundaries

| Layer | Owns | Must not require |
|---|---|---|
| x64base engine | Storage, indexing, low-level runtime behavior, metadata-capable structures. | LabTalk cases, storyboards, student examples, or publication media. |
| DotTalk++ runtime | Command shell, HELP, data navigation, work areas, relations, tuples, runtime proof. | Published LabTalk material. |
| LabTalk overlay | CASE catalog, teaching sequence, case studies, labs, storyboards, classroom/publication products. | Core engine changes unless a runtime behavior is genuinely missing. |
| SelfDoc/manualgen | Provenance, review gates, generated/manual publication products. | Unreviewed case content as final source truth. |

## Packaging Rule

Educational material belongs in optional overlay packages or clearly marked documentation paths. A build or runtime profile that only wants x64base/DotTalk++ professional behavior should remain usable without LabTalk source docs, case media, or storyboards.

## Runtime Rule

The CASE command may read normalized `docs/cases/CASE_*.md` records. Those records are derived catalog entries, not the source of truth. Source DOCX files, images, and deck files stay preserved as evidence and publication artifacts.

## Publication Rule

No case should be marked publication-ready until all of these are complete:

- source review
- factual review
- media review
- runtime/lab proof, when the case claims executable behavior
