# ETL Subject-Lane Charter V1 -- modern ETL, taught at inspectable scale

**Status:** review-needed draft (authored 2026-08-10, evening). Owner:
member.derald. Coauthor of record: member.ai.claude.cowork (Coworker, Class A).
AIF number: not yet claimed -- `claim-aif` is host-side; claim on adoption.
Sibling subject lanes: ACID (site: "ACID and the Glass-Box Engine"), Agile/SDLC
(campus SDLC material). Vehicle: the Cascade ERP learning micro-system
(`CASCADE_ERP_METADATA_ETL_LEARNING_GOLD_STANDARD_LANE_V1.md`).

## 1. The claim, at its honest tier

We demonstrate modern ETL **principles** where we have them, and demonstrate
their **absence** where we do not -- both runnably, both at a scale where every
stage is a file the student can open. We do not claim streaming, CDC, or DAG
orchestration; we demonstrate WHY they exist by exhibiting life without them.

## 2. Principles we demonstrate (present -- each with an existing proof)

- **Data contracts** -- the Cascade dual-carrier schema contract
  (`dual_schema_contract.json`); modern name for what the bundle already does.
- **Reconciliation / quality gates** -- SQLite as verification oracle
  (`SQLSEL_SELECT_V1`); derived-vs-declared checks (the rulings report,
  2026-08-10); G-guards and T-markers in the regression idiom.
- **Idempotent regeneration** -- tier0-refresh, `generate_dtschema.py`,
  "nothing on this page is hand-entered": re-run from canonical sources, get
  the same answer.
- **Lineage / provenance** -- sha256 source stamps in the `.dtgraph`;
  "generated from X" headers; evidence tiers on every public claim.
- **Layered stores (the medallion shape, at our scale)** -- meta sidecars
  (raw) -> DBF (typed, indexed) -> SQLite (verified serving copy), all three
  inspectable in the Cascade bundle.

## 3. Principles we demonstrate BY NEGATION (absent -- exhibits to build)

Method: **demonstrated negation** (glossary; owner-ratified 2026-08-10) --
teaching a concept by runnably exhibiting its absence; the deliberate sibling
of learning-by-failure. Each exhibit ends with "here is what a system that has
this must add."

- **No CDC:** change a DBF outside the pipeline; show nothing reacts until
  re-run. The absence, made visible, is the motivation for change-data-capture.
- **No orchestrator:** run two pipeline scripts out of order; show the failure
  mode. Motivates DAGs, dependencies, retries.
- **Batch cost:** time a full re-load vs the size of the actual change.
  Motivates incremental loads.
- **No streaming:** measure the staleness window between source change and
  serving-copy refresh. Motivates event pipelines.

These are exhibits, not apologies. A vendor curriculum cannot demonstrate its
own negative space; a learning macro-system can -- humility as a feature.

## 4. Founding exhibit (runtime-proven, 2026-08-10)

The pipeline that audited its own maintainers: the Open Rulings report (a
per-request ETL run -- extract ruling sheets, transform to derived counts, load
the view) caught its own maintainers' hand-kept footer drifted from the
measurement (declared 20, measured 18). Owner retired the footer the same
evening; sentinel `RUNNING-TOTAL RETIRED`, parser recognition, commit
`7a38c7fb8`. The incident stays visible on the page as story. Public faces:
the site's Cases and Storyboard live case; the proven-capabilities
"Self-measuring governance" entry.

## 5. Sequencing

1. Adopt charter; claim AIF (host).
2. Wire the Section 3 exhibits as scripted labs in the Cascade micro-system
   (each one a short `.dts` + expected transcript; promote per the
   promote-final-tests rule where an assertion is checkable).
3. Site subject page beside ACID when exhibits exist -- not before (the page
   must not outrank its proofs).

## 6. Doctrine this lane depends on

Two house graphs; two name planes; evidence tiers; no perishable literals;
demonstrated negation; learning micro/macro-systems. All: glossary
(`labtalk/ai_portal/AI_GLOSSARY_V1.md`), each pointing to its home.
