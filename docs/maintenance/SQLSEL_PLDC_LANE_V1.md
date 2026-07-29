# SQLSEL Product Lane -- PLDC Charter and Official Plan of Record

**Status:** `active_development`
**Owner:** `member.derald` - **Steward/author:** `member.ai.claude.cowork`
**Intake:** AIF-074 - **Claim:** `coordination/aif/AIF-074.claim` - **Run:** `SQLGOLD-SCOPING-20260729`
**Parent project:** `project.x64base.runtime` (a `project.x64base.sqlsel` promotion is drafted
as a candidate in the AIF-074 change package, per AIF-040 doctrine; owner decides)
**Plan of record:** `IMPLEMENTATION_PLAN_SQLSEL_V1_20260729.md` in the AIF-074 change
package (`outputs/2026-07-29_claude_gold_standard_sql_integration/`), summarized in Sec. 4.

---

## 1. Lane identity and lifecycle placement

SQLSEL is the **set-oriented SQL surface of the x64base Open Relationship Platform**
(ruling R11): a consumer library over the engine (R10), peer to the native REL browse
family, x64/XDBF + CDX->LMDB only (R4).

Lifecycle placement per `SDLC_FAST_START_SEED_V1.md`:

| Layer | Owning lifecycle |
|---|---|
| Engine seams, mode, statement surface, DML (phases P0-P5) | **DotTalk++ SDLC**, each phase run as a full **PDLC** (analyze -> design -> code -> test/debug -> document -> maintain) |
| Product packaging: library identity, own manual family, HELP, website claims, LabTalk lessons (phase P6) | **PLDC**, gated on the SDLC evidence beneath it -- PLDC cannot outrun SDLC proof |

## 2. Rulings ledger (owner rulings binding on this lane)

| # | Ruling |
|---|---|
| R1 | OG SQL effort predates engine maturity; **start new, keep the `SQLSEL` name**; the corpus scripts' intended `SQLSEL SELECT ... FROM ...` form becomes the real contract |
| R2 | Engine-mechanics assimilation precedes SQL design (survey Part 1 done; remaining items fold into each phase's analyze step) |
| R3 | **No wheel reinvention.** Consume proven implementations (locks, WAL, tuple system, expr/); a named, verified gap is the only license for new machinery |
| R4 | **x64/XDBF flavor only**; x32 only if free via shared seams |
| R5 | Clause identities via `@dottalk.subusage`: `sqlsel.select`, `sqlsel.from`, `sqlsel.where`, ... -- grammar introspectable from the engine |
| R6 | **SQL mode**: `SELECT` aliases to SQLSEL in SQL mode; native `SELECT` untouched in native mode; canonical names mode-invariant, only aliases modal |
| R7 | Mode switch: **`SET MODE SQL\|NATIVE\|OTHER`**; open enum; session-only; prompt-marked; never persisted in workspace files |
| R8 | SQL mode **hard-blocks** `REL`/`SET RELATION`/auto-refresh with corrective errors |
| R9 | `DELETE` modal alias **after** SQLSEL proves the pattern (plan: P5) |
| R10 | **SQLSEL is a consumer; the engine is core.** Own library + manuals via the same harvest pipeline; anything the engine lacks, the engine gains through its own gates |
| R11 | **Open relationship platform**: REL, SQLSEL, future consumers (graph, CODASYL) are peers over shared engine seams |

Catalog ruling: `.dtschema` is the catalog, read declaratively in SQL mode (RELATION
lines = join edges; machinery blocked per R8); `.graph` only ever as a **generated**
projection, never a hand-authored sibling authority.

## 3. Standing disciplines (adopted, enforced per phase)

1. **`consumes:` / `searched-and-absent:`** on every component in every design doc. No
   third value. (PDLC analyze-phase enforcement; see the AIF-074 pattern/proof doc.)
2. **Definition of done** per `AI_ENGINEERING_STANDARDS_SEED_V1.md` Sec. 3, all eight
   items, per phase: contracts (authored `experimental`, flipped `supported` only at a
   green gate -- the flip is the publish), regression authored+registered, proofs.yaml
   `runtime_observed` rows, RUN row, intake row update, closeout with envelope, lane-doc
   update, runbook where an operational surface is left.
3. **Delivery:** Outside-AI change packages; owner applies/commits; long builds are
   operator handoffs with recorded command/exit/artifact evidence.
4. **ASCII only, no em-dashes**, verified by grep before delivery.
5. **`contract_parser_gate.py`** (AIF-073 package) stays clean tree-wide at every gate.

## 4. Phase register (summary; the plan of record carries the detail)

| Phase | One line | Gate |
|---|---|---|
| P0 | Demote phantom SQL contracts (8 files, `supported` -> `experimental`); consolidate 5 duplicated helpers; resolve `cli::AliasRegistry`; run the AIF-073 harness | G0 |
| P1 | Engine seams: PRIMARY/UNIQUE metadata (4 consumers), TupleRow type surface + null ruling (OQ-2), truncation honesty (RDB-06), typed equality, first production `seek()` consumer (+PS-01 gate) | G1 |
| P2 | `src/sqlsel/` library target; `SET MODE`; `SELECT` router; R8 block; expression-fallback interception | G2 (`SQLMODE_SMOKE`) |
| P3 | Single-table `SELECT` (projection/WHERE/ORDER/LIMIT/COUNT) -> TupleRow streams -> existing renderers | G3 (SQLite oracle) |
| P4 | Joins: declared-edge validation/inference; chain nested-loop; index-nested-loop; minimal EXPLAIN | G4 (oracle + cross-algorithm identity) |
| P5 | DML + transactions as assembly: buffer/WAL, FLOCK, delta-based affected-rows, BEGIN/COMMIT/ROLLBACK verbs; `DELETE` alias (R9) | G5 (crash regression + oracle) |
| P6 | PLDC ascent: manual family, HELP, website promotion (closes OQ-9), LabTalk lessons, evidence gallery | G6 (nine-gate checkpoint) |

Out of scope, each returning as its own lane: outer joins (blocked by OQ-2), subqueries,
GROUP BY, x32 support, any second SQL dialect surface.

## 5. Open rulings, placed where they block

| Ruling needed | Blocks | Proposed default |
|---|---|---|
| OQ-2 blank-vs-NULL | P1.2; outer joins | blank-is-a-value, documented; no NULL literal in v1 |
| SET FILTER stance for SQL statements | P3 gate | statements ignore session filter; stated in contract |
| Bare `SQL` command disposition | P2.4 | retire after P0 demotion |
| Product name (SQLTalk?) | P6 | owner's call |

## 6. Registration state

- `coordination/aif/AIF-074.claim` -- applied with this charter.
- Intake row AIF-074 -- applied to `AI_INTERACTION_INTAKE_QUEUE_V1.md` with this charter.
- `labtalk/registries/ai_runs.yaml` RUN row -- see the AIF-074 registry-additions file;
  apply with care, the file may carry other in-flight modifications.
- `labtalk/registries/projects.yaml` promotion -- candidate only, owner decides.
- `docs/agents/CURRENT_TARGET.md` -- NOT modified by this lane; AIF-072 remains the named
  next target. This lane runs beside it by owner direction, stated here per the
  closeout-updates-startup rule rather than silently.

## 7. Provenance

This charter distills the AIF-073/074 record: 8 analysis documents, 2 tools (one run
clean tree-wide across 201 contract-carrying files), 11 owner rulings, a 7/7 measured
consumption pattern (reframed under PDLC by owner correction: investigation IS the
analyze phase), and an implementation plan in which exactly one component -- the
statement parser -- is `searched-and-absent`; everything else consumes. Evidence tier of
the lane at charter time: source_defined throughout; zero runtime evidence; first runtime
proofs are owed at G0.
