# MANUAL-ASSEMBLY -- the manual assemblage package + two public views (lane v1)

Status: **proposed / M5 done** (dev). Not promoted.
Owning lifecycle: DotTalk++ SDLC - source/HELP/SelfDoc -> manualgen -> manual + website.
Truth state: subsystem source-verified (2026-07-20); manifest built + validated.
Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-035).
Companions: AIF-032 (data-driven diagrams), AIF-033 (website content manifest),
AIF-034 (doc/SDLC model pin).

## Why this lane exists

The project makes a **self-documentation claim**: x64base uses its own metadata
and documentation infrastructure to describe and increasingly prove itself. Today
that claim is *mostly* real -- the 183-page command reference, the accepted
developer manual, the diagram attachment matrix, and the website catalog sync all
exist -- but the manual is produced by **~20 individually-invoked, human-gated
manualgen CLI steps** with **no single assembler**, and **nothing generates a
Table of Contents, Index, or Glossary**. The manual is a spine of harvested
catalogs plus authored chapters, stitched by hand.

To make the self-doc claim honest we have to *actually do it*: assemble the whole
manual from a declared bill of materials, weave in the generated diagrams and
front/back matter, and put **two views on the website** -- one showing the
assembly line running, one showing the manual it produces.

## The model: spine + branch (per AIF-034)

The manual is not one uniform artifact. It is:

- a **generated spine** -- command reference, function reference, SET family,
  error/message catalog: mechanically harvested from source/HELP/metadata; and
- an **authored branch** -- the narrative chapters (data model, indexing,
  expressions, dispatch, evidence) that teach *beyond* what can be harvested; and
- **generated front/back matter** -- title, provenance, TOC, glossary, index,
  colophon -- that today does not exist at all.

The spine is `generated`/`derived` (simplex, source->manual). The branch is
`maintained`/`derived`. A reviewed **duplex** edge (`D-web`, per AIF-034) may
later carry website-originated reader-orientation prose *into* the manual -- but
behaviour truth never travels that edge; it always returns to source.

## The assemblage package (the bill of materials)

`tools/manualgen/manual_assembly_manifest.yaml` (schema
`dottalk.manual.assembly_manifest.v1`) is the recipe: every part in reading
order, each carrying `kind` (frontmatter/spine/article/diagram/backmatter),
`class` and `direction` (**shared verbatim with the website manifest** so both
sit on one simplex/duplex spine), `source_of_record`, `generator`, `proof_label`,
`status` (exists/greenfield), and `output`.

Validated shape: **22 parts -- generated 7, derived 8, maintained 5, reported 3;
13 exist, 10 greenfield (the +1 maintained/greenfield is the `bm-ai-portal` appendix, added 2026-07-21).** The 9 greenfield parts are the honest gap:

| Greenfield part | Why it doesn't exist yet |
| --- | --- |
| `fm-title`, `fm-provenance` | no generated title/attestation page |
| `fm-toc` | **no TOC is generated** -- only discussed in prose |
| `fm-preface` | no authored preface part |
| `spine-function-reference` | function surface feeds the *website* catalog, not a bound manual reference |
| `spine-error-catalog` | error/message catalog not emitted as a manual part |
| `bm-glossary` | **no glossary** (note: `commands/glossary.md` is the GLOSSARY *command*, not this) |
| `bm-index` | **no index** is generated |
| `bm-colophon` | no build-provenance colophon closing the self-doc loop |

## The assembler (lane M3)

A single manifest-driven runner that, in manifest order:

1. runs each `generated`/`derived` part's generator into its part (never outside
   its region), reusing existing manualgen builders where they exist
   (`build-command-reference-candidate`, section builders) and adding the
   greenfield generators (TOC, glossary, index, colophon, title/provenance);
2. binds the 183 command pages and the diagram set (from the attachment matrix)
   into the reader instead of only linking them;
3. leaves `maintained` parts untouched (review-gate only);
4. appends `reported` parts (evidence, provenance) without overwriting;
5. emits the exports: `.md` (primary), on-site HTML reader, and PDF (M5).

It does **not** bypass the existing gates -- it orchestrates the candidate build;
acceptance/apply stays gated exactly as manualgen does today.

## The two public views (lane M5) -- two new pages

Decided 2026-07-20: **two new pages**, MD + PDF exports.

1. **Assembly-process view** -- *"How the manual assembles itself."* An
   educational page that renders the bill of materials (spine vs branch vs
   front/back matter), the direction x class of each part, the assembler
   pipeline, and the manual<->website sync. This page *is* the self-doc claim made
   visible. Class `derived` (tracks the manifest); lives under `docs/dev`.

2. **Rendered-manual reader** -- the assembled manual itself, viewable on the site
   (HTML) with `.md` and PDF downloads. Class `generated` (from the assembler
   output); staged via the existing `build_website_feed_packet.py` downloads path
   (`/downloads/current/...`) extended for the reader route.

## Maintenance / drift gate (lane M4)

Per-class gates on the fullstack push, mirroring the website manifest gate:

- `generated` parts -- regenerate every push; **drift gate fails the build** if a
  part's content != its `source_of_record` (extends the AIF-025 catalog checks and
  the AIF-032 diagram check to the manual).
- `derived` parts -- flag regenerate-or-review when `source_of_record` changes.
- `maintained` parts -- review task when the tracked subject changes.
- `reported` parts -- append-only; provenance is the gate.

## Milestones

- **M1 -- bill of materials. DONE (2026-07-20).** `manual_assembly_manifest.yaml`
  built and validated (22 parts; 9 greenfield identified). Grounded in the real
  published sections, the 183-page reference, and the diagram attachment matrix.
- **M2 -- part contracts + anchor convention. DONE (2026-07-20).** Every part now
  carries a stable anchor (`MAN-*`), a region mode (whole-file / candidate /
  authored / append / bind), and a generator binding (9 reuse manualgen, 13 bind
  to 8 new assembler modules). Anchor convention + greenfield generator I/O
  contracts: `docs/maintenance/MANUAL_ASSEMBLY_M2_PART_CONTRACTS_V1.md`. Manifest
  extended + re-validated (18 unique anchors; TOC/index run-last dependency noted).
- **M3 -- the assembler. DONE (2026-07-20).** `tools/manualgen/assemble_manual.py`
  reads the manifest, dispatches on region mode, and emits a real assembled manual
  (`generated/assembled/developer_manual_assembled_v1.md`) plus an
  `assembly_report_v1.json`. First build: **22/22 parts, 13,772 lines, anchors
  balanced 18/18**; all 8 greenfield generators produced real content -- 63
  functions harvested from `function_catalog.cpp`, 183 command pages bound, 12
  diagrams bound from the matrix, generated TOC/glossary/index, and a **colophon
  that records how the manual assembled itself** (assembler version, source commit
  `8ee746de`, attested machine). Acceptance stays gated; output lands in
  `generated/`, never `published/`.
- **M4 -- drift gate. DONE (2026-07-20).** `tools/manualgen/check_manual_drift.py`
  re-assembles fresh from current source, slices both manuals into per-part MAN
  regions, normalises build timestamps, and compares. Per-class severity:
  **generated/bind drift = FAIL** (nonzero exit, blocks the push); derived
  (candidate) / maintained (authored) / reported (append) drift = REVIEW
  (non-blocking regenerate-or-review); static = skip. Proven end to end: clean
  PASS (22 parts), a corrupted generated region flips it to FAIL and names the
  part, restore returns to PASS. Report: `generated/assembled/drift_report_v1.json`.
  Required uniform anchoring (M4 refinement): every part is now bracketed for
  tooling -- authored regions carry `gen=authored` and are never rewritten.
- **M5 -- two public views + exports. IN PROGRESS (2026-07-20).** Done: the
  assembler now emits **MD + PDF + HTML** (pandoc/xelatex), and
  `tools/fullstack_docs/stage_assembled_manual_to_site.py` stages all three to the
  site under **stable "latest" filenames** (`/downloads/current/developer-manual-latest.{md,pdf,html}`
  + `DEVELOPER_MANUAL_LATEST.json`) -- permalinks that every rebuild overwrites, so
  the link always resolves to the newest build. The downloads page carries a
  clearly-labeled "Latest assembled manual (always current)" section (assembled-
  candidate, distinct from the accepted baseline). The two *dedicated* educational
  pages are now built and sidebar-wired: `content/docs/dev/manual-assembly.mdx`
  ("How the Manual Assembles Itself" -- the assembly-process view) and
  `content/docs/dev/developer-manual.mdx` (the reader landing with the always-latest
  links). Site stays in `D:\dev` until the engine is pushed. A development lesson
  capturing the shift is recorded at
  `docs/maintenance/MANUAL_ASSEMBLY_HISTORIFY_OLD_TO_NEW_V1.md`.
- **M6 -- retire the hand-stitch.** Replace the ~20-step manual sequence with the
  assembler; the accepted-artifact acceptance becomes a gate over its output.

## Non-goals / honesty

The assembler orchestrates the *candidate* build; **acceptance stays human-gated**
-- this lane does not auto-publish the manual. `maintained` chapters remain
hand-authored on purpose. TOC/glossary/index are generated but their definitions
and final order are **reviewed**, not blindly shipped. Python 3.12+ (manualgen
already requires it); dev-only until built + proven.

## Provenance pointers

- Manifest: `tools/manualgen/manual_assembly_manifest.yaml`.
- Manual driver: `tools/manualgen/manualgen.py` + `manualgen_lib/` (dry_run,
  parity, selective_merge, command_reference_candidate, publication_structure).
- Publication root:
  `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/`.
- Diagram matrix:
  `docs/manuals/developer/manualgen/reports/diagram-publication-attachment-matrix-v1.csv`.
- Accepted artifact:
  `docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json`.
- Downloads staging: `tools/fullstack_docs/build_website_feed_packet.py`.
- Shared vocabulary: `tools/fullstack_docs/website_content_manifest.yaml` (AIF-033).
- Assembler + gate: `tools/manualgen/assemble_manual.py`,
  `tools/manualgen/check_manual_drift.py`.
- Site staging: `tools/fullstack_docs/stage_assembled_manual_to_site.py`.
- Development lesson: `docs/maintenance/MANUAL_ASSEMBLY_HISTORIFY_OLD_TO_NEW_V1.md`.
