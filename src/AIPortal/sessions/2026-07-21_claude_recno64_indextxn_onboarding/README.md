# AI Session Collection — 2026-07-21 (Claude / Cowork)

**Status: UNREVIEWED CANDIDATE MATERIAL. Not authority. Not promoted. Not built.**
Collected into the `src/AIPortal/` collection point per `AI_README.md`. This is raw
AI-interaction material — it must still be *classified, distilled, anchored, routed,
and reviewed* before any of it becomes a contract, lane record, or source change
(`AI_PORTAL.md` → Working Rules).

**Agent:** Claude (Cowork, local-access). **Authorization:** maintainer granted "catalog
your files into my local repo" (cataloging only — no source mutation, no promotion,
no dashboard/intake/projects.yaml edits were made).

## What's here
- **`_SESSION_INDEX_AND_CURATION_V1_20260721.md`** — the catalog / table of contents.
  Read it first: it groups everything by lane, flags superseded drafts, and lists the
  AIF disposition + next gate for each item. (Its opening line predates filing; as of
  this collection the material is **collected here**, still **not promoted**.)
- `*.md` — findings, lane docs, change packages, steward package, audits, logs.
- `*.patch`, `*.dts` — candidate diffs and a regression script.
- `candidate_source/*.txt` — candidate **source drafts** with a `.txt` suffix so
  `src/CMakeLists.txt` `GLOB_RECURSE` cannot compile them. Strip `.txt` only after review.

## Grounding caveats (read before trusting any item)
- Early analysis was against the **public GitHub snapshot**, not `D:\code\ccode`.
  The RECNO64 carriers were later reconciled against dev and **match** (O11
  `cdx_backend.cpp:863`, BUILDLMDB `cmd_buildlmdb.cpp:445`, `order_step_cdx`
  `order_iterator.cpp:407`), plus one dev-only find (`cmd_indexseek.cpp`). The
  Lane A (`SET INDEXTXN`) source drafts are still **snapshot-based — re-ground vs dev**.
- No baseline commit captured yet; attach one (`git -C D:\code\ccode rev-parse HEAD`)
  before any of this is proposed for promotion.

## Three candidate lanes inside (see the index for detail)
1. **`SET INDEXTXN` transactional index maintenance** (relates to AIF-023 CDX/LMDB reconciliation).
2. **RECNO64 nav/index residual** — AIF-027 follow-on. **Drift flagged:** the AIF-027
   dashboard "M4-5 done" is a sparse *storage* proof; *index/nav* addressing past 2³¹ is open.
3. **New-chat onboarding trigger + `AI_README` Cowork-access insert** (AIF-006 family).

## Not done (maintainer-gated)
Promotion into the reviewed system of record — `AI_INTERACTION_INTAKE_QUEUE_V1.md`
(intake rows), `AI_FRIENDLY_DASHBOARD_V1.md` (lane rows + Session Log), `projects.yaml`,
`CURRENT_TARGET.md`, a `docs/maintenance/SESSION_CLOSEOUT_*` — none of which was touched.
That step is proposed/reviewed/promoted, never self-certifying.
