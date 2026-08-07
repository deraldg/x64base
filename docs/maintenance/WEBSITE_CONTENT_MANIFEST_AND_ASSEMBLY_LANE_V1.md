# WEBSITE-ASSEMBLY -- content manifest + assembly & maintenance stream (lane v1)

Status: **active foundation** (dev). Manifest v2 and current-work projection
implemented 2026-07-23; full assembly automation remains open. Not promoted.
Owning lifecycle: DotTalk++ SDLC - fullstack documentation -> website.
Truth state: gap source-verified (2026-07-20); no source yet.

## Why this lane exists

Website upkeep is currently a **reactive, page-by-page pass**: when the engine
changes, a human (or AI) hunts for stale prose and hand-edits it. That is a sparse
sweep -- it drifts, it is not repeatable, and it does not distinguish a page that
*should be generated* from one that is *meant to be hand-authored*.

The ingredients for a systematic layer already exist, but scattered:

- `x64base-site/content/docs/dev/website-documentation-matrix.mdx` -- a
  human-readable **Section Matrix** and **Feed Matrix**.
- **Direction Gates** and **Proof Rules** (see
  `selfdoc-website-publication.mdx`).
- **Harvest anchors** on generated pages (`DIAG-ERRCODE-010`, `DIAG-X64GEOM-005`,
  ...) with per-page "regenerate or review" notes.
- `tools/fullstack_docs/*` generators (command/function catalogs, etc.).

What is missing is (1) a **single machine-readable manifest** that classifies
every page/region, and (2) an **assembly-and-maintenance stream** that acts on it.

## The classification (the vocabulary)

Every page -- and every anchored region within a page -- is exactly one class:

| Class | Meaning | Maintenance rule |
| --- | --- | --- |
| **static** | Hand-authored, no source derivation (branding, positioning, screenshots-as-artifacts). | Human review only; changes are deliberate. |
| **maintained** | Hand-authored but *tracks a source subject* (architecture prose, capacity-math lesson). | Review-gate: flag for refresh when the tracked subject changes. |
| **maintained_current** | Permanent route whose present-state region changes over time (current work, project truth, roadmap, active documentation vertical). | Reconcile from named authorities; replace the current region; expose an `as_of_date`, proof state, and next gate; preserve linked event history. |
| **derived** | Assembled by transformation from source evidence, with human framing (reframed engine pages, feature crosswalk). | Regenerate-or-review when the source-of-record changes. |
| **generated** | Emitted verbatim into anchored regions from source (command/function catalogs, error codes, messaging catalog, data-carrying diagrams). | Regenerated on the fullstack push; **hand-edits inside anchors are forbidden**. |
| **reported** | Provenance-bound snapshots of a report/measurement (Pinocchio benchmarks, documentation-progress, machine profile). | Append-only; provenance pinned; never silently overwritten. |

## The manifest

One machine-readable file (candidate: `tools/fullstack_docs/website_content_manifest.yaml`,
mirrored to the site) with one entry per page **and per anchored region**, recording:

- `path` (and `anchor` id for a region within the page),
- `class` (static / maintained / maintained_current / derived / generated / reported),
- `source_of_record` (the source path(s) / registry / report it derives from, or
  `none` for static),
- `generator` (for generated/derived: the fullstack tool + mode that emits it),
- `proof_label` (the Proof-Rules label it may carry),
- `direction_gate` (simplex / duplex-reviewed / website-owned exception),
- `last_verified` / `last_generated`.

The existing `website-documentation-matrix.mdx` becomes the **human-readable view**
of this manifest, not a separate hand-maintained list.

## Assembly stream

The fullstack push, driven by the manifest:

1. For each **generated** / **derived** entry, run its generator and write the
   result into the page's anchored region only (never outside the anchor).
2. Leave **static** and **maintained** pages untouched.
3. For **maintained_current** entries, reconcile the replaceable present-state region
   from its named registries or ledgers. Advance the `as_of_date` only after readback;
   never rewrite a historical event date to make it look current.
4. For **reported** entries, append the new snapshot from its report with
   provenance; do not overwrite prior rows.
5. Byte-sync generated assets (SVGs, catalogs) into the site and verify sync.

## Maintenance stream

Per-class gates, wired into the fullstack push and the pre-publish checklist:

- **generated** -- regenerate every push; a **drift gate** fails loudly if an
  anchored region's content != its current source (extends the AIF-025 catalog
  checks and the AIF-032 diagram check).
- **derived** -- when a `source_of_record` changes, flag the page
  regenerate-or-review; do not let it silently rot.
- **maintained** -- when the tracked subject changes, raise a review task.
- **maintained_current** -- reconcile current status, evidence state, owner, and next gate
  from named authorities; stale `as_of_date` is a review failure.
- **reported** -- append-only; the provenance/attestation is the gate.
- **static** -- human review only; excluded from drift checks.

## Milestones

- **M1 -- taxonomy + manifest. DONE (2026-07-20).** All 108 pages classified onto
  the direction x class grid (maintainer-resolved) and locked into a machine-readable
  manifest, `tools/fullstack_docs/website_content_manifest.yaml` (validated: generated 6,
  derived 23, maintained 54, reported 6, static 19 = 108; full coverage). Human view +
  per-page source-of-record: `docs/maintenance/WEBSITE_CONTENT_MANIFEST_M1_CLASSIFICATION_V1.md`.
- **M1a -- maintained-current class + live work view. DONE (2026-07-23).** Manifest
  v2 classifies 117 pages, introduces the permanent-but-current contract, and generates
  Current Tasks & Projects from `projects.yaml` plus `ai_portal_tasks.yaml`. Pseudo-Chat
  remains a return lane and is projected as an inbox, not a competing authority.
- **M1b -- historical source museum. DONE (2026-07-23).** The SHA-256-bound
  `xbase.zip` archive generates a 21-file, read-only source browser with byte hashes,
  archive timestamps, public-safe manifests, and plain-text inspection links. The
  family tree is a separate reported page; CSV/JSON are labeled downloads, not pages.
- **M2 -- anchor convention.** Formalize the harvest-anchor convention for every
  **generated** region and map each to its owning fullstack generator/mode.
- **M3 -- assembly runner.** Build the manifest-driven assembler: read manifest ->
  run generators into anchors -> byte-sync to the site.
- **M4 -- maintenance/drift gate.** One drift check per class, run on the fullstack
  push and in the pre-publish checklist; a generated region that disagrees with
  source fails the build (as the catalog checks already do).
- **M5 -- retire the sparse pass.** Replace reactive page-by-page editing with the
  manifest-driven stream; the documentation matrix becomes the manifest's view.

## Non-goals / honesty

Not every page becomes auto-generated -- **static** and **maintained** pages stay
human-authored on purpose. This lane classifies and governs; it automates only the
**generated** / **derived** / **reported** classes and makes drift a build failure
rather than a manual hunt. Requires Python 3.12+ (fullstack tools already do); dev
env, not the CI sandbox. Dev-only until built + proven.

## Provenance pointers

- Human matrix today: `x64base-site/content/docs/dev/website-documentation-matrix.mdx`.
- Gates/labels: `.../selfdoc-website-publication.mdx`, `.../website-documentation-matrix.mdx`.
- Generators: `tools/fullstack_docs/*`; drift precedent: AIF-025 (catalog checks),
  AIF-032 (data-driven diagrams).
- Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-033).
