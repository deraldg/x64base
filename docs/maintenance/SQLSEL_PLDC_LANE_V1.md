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
| R12 | **expr is the preferred expression engine** (owner, 2026-07-29). A simpler boolean evaluator exists beside it; all SQLSEL evaluation routes through expr, and the two-evaluators defect (RT-02/RT-02a, three runtime sightings) is engine consolidation work, not something to code around |
| R13 | CALC, CALCWRITE, and REPLACE already carry table buffering for recovery/commit/recall (owner note, 2026-07-29) -- SQLSEL DML consumes an already-buffered seam; statement-scoped wiring is the only new part |
| R14 | **No OS-dependent code baked into lane deliverables** (owner, 2026-07-29). Portable standard C++ only; where a platform seam is unavoidable, use the tree's existing guarded-code convention, never inline platform assumptions. MSVC and WSL builds are both first-class |
| R15 | **Mission to completion** (owner, 2026-07-29): delay and restart degrade team performance. Within a phase, execute unblocked items continuously; do not park work awaiting ceremony. Blocked items (owner rulings) queue without stalling the rest |
| R16 | **Orthogonality at the apex** (owner, 2026-07-29): design axes must not entangle. Derived rulings, closing four open questions at once: (a) **OQ-2 CLOSED** -- blank-is-a-value; the value model is ENGINE-owned and mode-invariant; no NULL literal in v1 (NULL semantics would entangle mode with data meaning; may return as its own lane). UNBLOCKS P1.2. (b) **SET FILTER stance CLOSED** -- SQL statements ignore session filter state; statement semantics and session state are separate axes; stated in the SQLSEL contract. (c) **Bare `SQL` CLOSED** -- retired; mode switching has exactly one owner, `SET MODE` (R7); no overlapping verbs. Closes P2.4. (d) **Null-concat silence CLOSED** -- report, never silently coerce; error state and value state are separate axes (a blank VALUE concatenates as itself per (a); an evaluation FAILURE reports). Unblocks the P1.6 item. Product name (P6) remains open -- non-semantic, no orthogonality stake |

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
| P1 | Engine seams: PRIMARY/UNIQUE metadata (4 consumers), TupleRow type surface + null ruling (OQ-2), truncation honesty (RDB-06), typed equality, first production `seek()` consumer (+PS-01 gate), P1.6 route projection/print expression terms through expr (R12; until it lands, SQLSEL v1 projection is bare columns only with corrective errors) | G1 |
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
clean tree-wide across 201 contract-carrying files), 13 owner rulings, an 8/8 measured
consumption/correction pattern (reframed under PDLC by owner correction: investigation IS
the analyze phase), and an implementation plan in which exactly one component -- the
statement parser -- is `searched-and-absent`; everything else consumes. Evidence tier at
charter time was source_defined throughout; Sec. 8 records the first runtime evidence.

## 8. Runtime evidence log (post-charter)

**2026-07-29, harness runs 1-2** (`rdb_truth_proof_v1/v2.dts` + scorer, operator-run;
transcripts `rdb_truth_transcript*.txt`, reports `rdb_truth_report*.json` at repo root;
full record: `G0_RUN1_EVIDENCE_RECORD_V1_20260729.md` in the AIF-074 package):

- Run 1 = fixture-failure run, correctly voided by its own reading rule. Yield: SQLite
  oracle proven end-to-end; RT-02 found (bare booleans stringify empty in the `?` path;
  comparisons render `.T./.F.`); RT-01 raised and then RESOLVED AGAINST THE HARNESS --
  bare `USE` opens into the CURRENT area (`cmd_use.cpp:504,563`), classic xBase; not an
  engine defect. Correction #8 in the pattern ledger, self-caught. Doc-gap candidate:
  one readiness-rules line stating the semantics.
- Run 2 (v2: SELECT 1..5 before each USE; comparisons-only markers) = **clean
  confirmation run: PASS exit 0; 11/11 Tier A, 4/4 derived, 7/7 oracle blocks.**
  Findings RDB-01, -02, -03, -04, -05(A/B/C), -07, -10, -12 promoted from
  source_defined to **runtime_observed**; RDB-14 self-relation survival observed.
  Two scorer defects found+fixed by runtime (prompt-prefix strip; stacked prompt dots
  from silent lines).
- RDB-10 hand check over-delivered: `TUPLE ALLTRIM(f)` emitted empty values -- the
  projection expression was never evaluated. Third sighting of the two-evaluators
  defect; consolidated under R12 as P1.6.
- **Gate status: G0 harness/oracle component proven; G0 itself remains OPEN** pending
  P0.1-P0.3 code work (an earlier "G0 green" wording was corrected by the adversarial
  pass, AP-4).

**2026-07-29, later same day: GATE G0 CLOSED -- GREEN.** Evidence:

- P0.1 applied+committed (a401c1470): 8 early-SQL contracts supported -> experimental.
  `contract_parser_gate.py --union` PASS post-demotion (canonical invocation is --union;
  per-file mode false-positives on cross-file dispatch).
  CORRECTED (owner, same day): the flip IS the whole action; publication state
  (HELP/META/manual de-advertisement) propagates and is verified at the NEXT
  documentation full-stack push by that pipeline's own gates. The operator HELP
  spot-check originally cited here was weak evidence (live help store not yet
  re-harvested) and was unnecessary. Doctrine adopted for the lane: verification
  proportional to change class -- contract flips: commit gates + next docflush;
  dead-code deletion: build green; shared-path code changes: targeted or full
  regression (REGRESSION ALL here was warranted by P0.2, not P0.1).
- P0.3 applied+committed (same commit): 3 dead AliasRegistry headers + orphan
  command_join_alias.cpp removed (zero includers/references, verified).
- P0.2 applied+committed (12269891e): cli::workarea_util consolidation, REL re-pointed,
  net -36 lines; g++ -fsyntax-only clean on all 4 TUs pre-handoff.
- P0.4 done (harness runs 1-2, Sec. above).
- Operator evidence: MSVC Release build green; **REGRESSION ALL green** (NONDESTRUCTIVE,
  INDEX_X32, INDEX_X64, X64_METRICS, LANGUAGE, DOTSCRIPT_EXPR, DOTSCRIPT_PARITY, LEXING
  -- every self-asserting marker .T./PASS), exercising the consolidated paths directly
  (by-name SELECT, REL LIST/REFRESH). Normalization guards: 0 guarded phantoms, no
  fail-lane findings, both commits.
- workarea_util contracts flipped experimental -> supported per the flip-at-green-gate
  rule (the flip is this gate's publish action).

Phase P0 is CLOSED. Next: P1 (engine seams), opening with P1.1 PRIMARY/UNIQUE KEY
metadata; owner rulings OQ-2 (blank-vs-NULL) blocks P1.2.

**Adversarial pass on the plan of record** (task-17 discipline, 2026-07-29): plan
structure survived; 6 corrections (2 substantive: a cited regression filename that does
not exist -- G5 respecified against `commit_rollback_test.dts` + the pinocchio WAL phase
proofs -- and the AP-4 gate overclaim). Full appendix in the plan document.
