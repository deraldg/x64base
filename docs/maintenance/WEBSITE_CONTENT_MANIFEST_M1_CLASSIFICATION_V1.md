# WEBSITE-ASSEMBLY M1 — proposed content classification (v1, for review)

Status: **proposed first cut** (2026-07-20). Read-only; no tooling wired.
Companion to `WEBSITE_CONTENT_MANIFEST_AND_ASSEMBLY_LANE_V1.md` (AIF-033).

Every one of the 108 `content/**` pages is placed on the **direction × class**
grid. This is a proposed map to see the shape before building the manifest/runner;
rows marked **(confirm)** are my best guess and want a maintainer decision.

**Direction** (the simplex/duplex spine): `S-impl` = simplex, implementation →
website · `S-rep` = simplex, report/measurement → website · `D-man` = duplex,
reviewed manual → website · `WO` = website-owned (no upstream authority).

**Class**: static · maintained · derived · generated · reported.

## Shape at a glance (proposed)

| Class | Count | What it means for assembly |
| --- | ---: | --- |
| generated | 6 | Run a generator into anchored regions every push; hand-edits inside anchors blocked. |
| derived | ~13 | Regenerate-or-review when source-of-record changes; human framing allowed. |
| maintained | ~45 | Review-gate on subject change; hand-authored. |
| reported | ~7 | Append snapshot + provenance; never overwrite. |
| static | ~37 | Human review only (brand, positioning, news, most product pages). |

The headline: **only ~6 pages are truly generated today**; the reframe work this
week was almost entirely `derived`/`maintained` prose — exactly why it was a
hand-hunt. The lane's value is turning the ~19 generated+derived pages into a
push-driven, drift-gated set and leaving the ~82 human pages clearly labeled.

## generated — emit from a fullstack generator into anchors (`S-impl`)

| Page | Source-of-record / generator | Proof |
| --- | --- | --- |
| docs/dottalk/command-catalog | registry `shell_commands.cpp` + `@dottalk.usage` → `command_catalog_sync.py` | generated-reviewed |
| docs/dottalk/function-catalog | `function_catalog.cpp` + student autoreg → catalog generator | generated-reviewed |
| docs/dottalk/command-families | command registry family grouping | generated-reviewed |
| docs/engine/error-codes | HRESULT catalog harvest (anchor `DIAG-ERRCODE-010`) | generated-reviewed |
| docs/engine/messaging-and-localization | message catalog + locale spine harvest | generated-reviewed |
| docs/dottalk/command-reference | manualgen 183-page reference | manual-reviewed **(D-man, confirm)** |

## derived — transformed from source, human framing (`S-impl`)

| Page | Source-of-record | Proof |
| --- | --- | --- |
| docs/engine/x64-capacity-math | trinity headers + RECNO64/limits status | generated-reviewed |
| docs/engine/dbf-64-specification | `xbase_64.hpp` / DBF_64 header layout + field-codec | source-evidenced |
| docs/engine/fpt64-memo-format | FPT64/DTX memo headers | source-evidenced |
| docs/engine/feature-crosswalk | SelfDoc engine feature crosswalk report | generated-reviewed |
| docs/engine/ecosystem-feature-comparison | crosswalk + ecosystem research | source-evidenced |
| docs/engine/architecture | engine layer source | source-evidenced |
| docs/engine/cdx-lmdb-indexing | index backend source | source-evidenced |
| docs/engine/api-reference | runtime/GUI/codec API surface | source-evidenced |
| docs/engine/sqlsel-and-sql-conformance | `include/sql_ref.hpp` x64 conformance field + `@dottalk.usage` contracts for SQLSEL/SQL/SQLITE + `REGRESSION SQLSEL_SELECT_V1` (SQLite oracle) | runtime-evidenced |
| products/sqlsel | SQLSEL statement contract + `docs/maintenance/SQLSEL_PLDC_LANE_V1.md` (R19 names the product, R20 publishes it) | source-evidenced |
| docs/talk-family/sqlsel | SQLSEL contract + lane doc + `docs/maintenance/BUFFER_VISIBILITY_TWO_FAMILIES_V1.md` (RelTalk/SQLsel distinction) | runtime-evidenced |
| docs/dottalk/data-mutators | REPLACE/CALC/COMMIT/buffer source | source-evidenced |
| docs/dottalk/dotscript-language-guide | DotScript command/HELP source | source-evidenced |
| docs/dottalk/set-family | `SET` command source | help-catalog-evidenced |
| docs/dottalk/syntax | grammar/parser source | source-evidenced |
| docs/dottalk/repl | real REPL transcripts | runtime-evidenced |

## maintained — hand-authored, tracks a source subject; review on change

`S-impl` review-gated. Engine & DotTalk++ conceptual pages, the talk-family
naming pages, getting-started, and the dev/labtalk process docs:

- docs/engine/acid-and-glass-box **(tracks WAL/durability state)**, runtime-footprint,
  xbase-ecosystem-context, dbf-flavors-and-indexes, indexing-rules,
  regression-and-proof-testing
- docs/dottalk/language-guide, curriculum, sdlc, examples
- docs/getting-started/overview, installation, quickstart, faq
- docs/talk-family/tuptalk, tabletalk, turbotalk, reltalk, arctic, arctictalk,
  parallel-gui-tui
- docs/dev/coding-standards, naming-conventions, contribution-guide,
  onboarding-guide, developer-handbook, developer-profile, application-ui-dsl-lane,
  public-site-architecture, recursive-co-development, selfdoc-website-publication,
  selfdoc-feed-pipeline, help-message-selfdoc-dfd, site-improvement-plan,
  third-party-acknowledgements, experimental, project-truth, important-documents,
  website-documentation-matrix
- docs/labtalk/academic-positioning, ai-portal, career-lessons, cases-storyboard,
  database-evolution, education-features, examples, lessons, lms-integration-lane,
  non-profit-guide, overview, selfdoc-lane, student-lessons, suggest-a-lesson

## reported — provenance-bound snapshots; append-only (`S-rep`)

| Page | Report / provenance |
| --- | --- |
| docs/engine/pinocchio-benchmarks | benchmark ledger + `PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json` (maintainer-attested) |
| docs/dev/documentation-progress | full-stack gate ledger + progress JSON |
| docs/dev/current-lanes | lane-state snapshot (dashboard) **(confirm: derived vs reported)** |
| docs/dev/historical-source-lineage | source-lineage seed CSV + checksums |
| docs/dev/roadmap | generated-reviewed from lanes/intake **(confirm: derived vs reported)** |
| docs/labtalk/runtime-evidence | screenshot/transcript evidence gallery |

## static — website-owned, no upstream authority (`WO`)

Human review only; excluded from source-drift checks:

- about/brand-story, contributors, mission-vision, origin-story, timeline
- brand/logo-concepts, trademarks, usage-guide, visual-identity
- news/announcements/* (6) and news/press-releases/* (4) — dated, immutable
  historical record
- products/arctictalk, dotscript, dottalk, labtalk, parallel-gui-tui, reltalk,
  tabletalk, tuptalk, turbotalk **(mostly static positioning)**; products/x64base-engine
  **(confirm: derived vs static — carries capability claims that track the engine)**

## Resolved (maintainer, 2026-07-20)

1. **command-reference → `generated` (`S-impl`).** The manual is generated from the
   fullstack doc suite (manualgen); it is not a hand-authored duplex artifact. It
   joins the generated class.
2. **roadmap + current-lanes → `reported` (`S-rep`).** Both are lane-state
   snapshots; report all current lanes with updates. Moved from derived to reported.
3. **product pages → `derived` (`S-impl`).** They carry capability claims that must
   track the engine. All `products/*` move from static to derived.
4. **Rest accepted as proposed** (e.g. `set-family`, `data-mutators` stay `derived`).

### Resolved shape

| Class | Count |
| --- | ---: |
| generated | 6 |
| derived | ~23 (incl. 10 product pages) |
| maintained | ~45 |
| reported | ~7 |
| static | ~19 (about, brand, news) |

The machine-readable manifest is `tools/fullstack_docs/website_content_manifest.yaml`.
