# SQLSEL Product Lane -- PDLC Charter and Official Plan of Record

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
| Product packaging: library identity, own manual family, HELP, website claims, LabTalk lessons (phase P6) | **PDLC**, gated on the SDLC evidence beneath it -- PDLC cannot outrun SDLC proof |

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
| R17 | **Two relational methodologies, reported distinctly** (owner, 2026-07-29). x64base carries TWO relation-facing surfaces over the same engine seams -- similar but different, peers not replacements (R11). **(a) REL / RelTalk:** cursor-oriented; correlated expansion from the CURRENT parent record; session-stateful (current area, record pointer, active order, filter); browse primitive by ruling (OQ-3); result is a traversal projection. **(b) SQLSEL:** set-oriented; statement-scoped; mode-gated (R7); ignores session filter/cursor state (R16b); result is a row set. **Shared beneath both:** catalog/dtschema, `cli::workarea_util` resolution, typed equality (P1.4), PRIMARY/UNIQUE keys (P1.1), the TupleRow carrier + type surface (P1.2), scan-limit honesty (P1.3), locking + TABLE BUFFER/WAL. **Reporting rule:** no publication surface (manual, HELP, website, curriculum, evidence caption) may let one methodology's claims stand for the other's behavior; where both are in scope, present the contrast explicitly. A side-by-side comparison table is a P6 deliverable and a natural teaching asset (cursor-vs-set is the curriculum's core lesson) |
| R16 | **Orthogonality at the apex** (owner, 2026-07-29): design axes must not entangle. Derived rulings, closing four open questions at once: (a) **OQ-2 CLOSED** -- blank-is-a-value; the value model is ENGINE-owned and mode-invariant; no NULL literal in v1 (NULL semantics would entangle mode with data meaning; may return as its own lane). UNBLOCKS P1.2. (b) **SET FILTER stance CLOSED** -- SQL statements ignore session filter state; statement semantics and session state are separate axes; stated in the SQLSEL contract. (c) **Bare `SQL` CLOSED** -- retired; mode switching has exactly one owner, `SET MODE` (R7); no overlapping verbs. Closes P2.4. (d) **Null-concat silence CLOSED** -- report, never silently coerce; error state and value state are separate axes (a blank VALUE concatenates as itself per (a); an evaluation FAILURE reports). Unblocks the P1.6 item. Product name (P6) remains open -- non-semantic, no orthogonality stake |
| R25 | **Platinum PRICED AND DEFERRED: engine-wide evaluator unification (2026-07-29).** The end state that permanently kills the two-families split is moving EVERY reader -- `DISPLAY`, `COUNT FOR`, `LOCATE`, `SCAN`, `SET FILTER` -- onto one evaluator, which would close OQ on SMARTLIST as a side effect because there would be only one way to read a row. It is deferred as PLATINUM on evidence, not nerves: those are the hottest paths in the engine and `PHASE0_DECODE_COST` already publishes the floor (SUM ~19.5s, COUNT FOR 3-term ~70.5s over the 1,000,000-row pinocchio fixture). Building a `TupleRow` per record across a million rows is unlikely to be free, and that benchmark would show it immediately; the blast radius is every scan command in a shipped engine, each needing its own regression. **A legitimate cheaper destination exists and should not be treated as failure:** if the benchmark shows tuple construction is fine on small tables and unacceptable at scale, the honest end state is a DOCUMENTED RULE assigning each command to a family, enforced by a gate, with SMARTLIST assigned deliberately instead of accidentally. That also closes the open SMARTLIST question, at a fraction of the cost |
| R26 | **FULL MODERN RELATIONAL ALGEBRA IS IN SCOPE (owner ruling, 2026-07-30; widened from the joins-only reading the same day).** The lane implements the complete algebra a modern relational engine is expected to offer, not a subset: selection and projection (P3, done); rename via aliases (P4.1); the full join family INNER / LEFT / RIGHT / FULL / CROSS (P4.0a-P4.4); DISTINCT and the set operations UNION / UNION ALL / INTERSECT / EXCEPT (P4.5); grouping and aggregation GROUP BY / HAVING / COUNT / SUM / AVG / MIN / MAX (P4.6); and subqueries, scalar and IN / EXISTS, uncorrelated then correlated (P4.7). Relational DIVISION gets no operator of its own because SQL has none -- it is expressed as NOT EXISTS over NOT EXISTS, so it becomes available with P4.7 rather than being invented. The owner accepted the stated cost: this ROUGHLY DOUBLES the lane, and P4.6 and P4.7 each raise a semantic question x64base has not answered before (OQ-10, OQ-12). Scope is now closed at the algebra boundary -- DML and transactions remain P5, and anything beyond the algebra (window functions, CTEs, recursive queries) is a later lane, not a silent extension of this ruling |
| R27 | **Declared relations are an OPTIMIZATION HINT, never a precondition (owner ruling, 2026-07-30; resolves the stale P4 roll-up row).** A join matches rows from its ON clause alone (R21), so any two OPEN tables join on any comparable columns with no prior SET RELATION and no registry lookup. Where a declared relation with a usable index happens to exist for the pair, P4.2 may use it to seek instead of scan -- same answers, faster path, and the path is REPORTED either way. SQLsel is therefore NOT a front end onto RelTalk; the two are independent surfaces over the same store. Requiring a declared edge, or silently inferring an ON clause from one, is rejected: it would make a correct SQL statement fail for a reason SQL has no vocabulary to explain |
| R28 | **OQ-10 RULED: aggregates SKIP blanks and REPORT the count (owner ruling, 2026-07-30).** Blank remains a value (R16 untouched), but a blank numeric field holds SPACES, and spaces are not a number -- reading them as zero INVENTS a data point nobody entered. Blanks are therefore excluded from numeric aggregation because they are NOT NUMERIC, not because they are null; this is a typing argument, not a NULL argument, which is why it does not reopen OQ-2. Every aggregate over a column containing blanks REPORTS the split -- `AVG(SALARY) = 50000.00 (160 of 200 rows carried a value; 40 blank)` -- following R22 (marker plus count) and P4.2 (access path reported every time): when a semantic choice is invisible in the output, PRINT IT. Decision scope confirmed by decomposition: `COUNT(*)` and `SUM` return identical answers under either rule (adding zeros changes no sum), so only `AVG`, `MIN` and `COUNT(col)` diverge. `MIN` is the sharpest case -- blanks-as-zero reports a lowest salary of $0 belonging to no employee. Keeps the SQLite oracle green at G4f with no per-case hand expectations |
| R29 | **NULL-READINESS: ship gold, pre-shape for platinum (owner ruling, 2026-07-30 -- "measure twice, cut once").** Stored NULL with three-valued logic is NOT implemented and NOT scheduled; R28 governs behavior today. But every schema, interface, contract and code path authored from here is SHAPED so that adding NULL later is an EXTENSION, not a rewrite. Rationale recorded so the discipline is not mistaken for a commitment to implement: NULL cannot retroactively disambiguate blanks already on disk (the 200 STUDENTS records carry no bit distinguishing "zero" from "never entered", and no later feature recovers information never stored), so a NULL lane would still owe an R28 ruling for legacy data AND would add a second regime on top of it. Sequencing also argues against implementing now: three-valued logic would sit on an expression engine that as of 2026-07-30 cannot parse `ALLTRIM(CVAL) = "ALPHA"` in the tuple path (ED-01) and loses `EMPTY()`'s type in the classic path (ED-02). Fix the foundation first. The readiness SEAMS are enumerated as standing discipline 6 |
| R24 | **P4.0 is seam-based, and the harness comes first (2026-07-29).** Load-bearing finding from the P4 survey: `expr::compile_bool_predicate(area, ...)` and `eval_bool_compiled(pred, area, ...)` **bind to a single `DbArea`**. A join's `WHERE` referencing both tables cannot be evaluated by the path SQLsel ships today. The multi-area evaluator is `expr_tuple_glue`, bound to `TupleRow`. That forces a choice that was NOT visible when R21 was ruled: SQLsel either keeps TWO evaluators (DbArea when unjoined, tuple when joined) or migrates wholly. **Two evaluators is option C one level down** -- the same `WHERE` could resolve fields or coerce types differently depending on whether a JOIN appears in the statement -- so it is rejected on the same evidence. Decisions: **(a)** P4.0 migrates SQLsel's `WHERE` to the tuple-bound evaluator with `overlay_table_buffer=false` to preserve R18 committed truth, gated by re-running G3 -- if the SQLite oracle still matches row-for-row, the migration changed nothing, which is the payoff for having built that gate; **(b)** P4.0 introduces a predicate-evaluation SEAM (one interface, two implementations) rather than a direct call, because the seam is what makes platinum reachable incrementally instead of as a rewrite; **(c)** the DIFFERENTIAL HARNESS is built BEFORE the seam. Rationale for (c) is asymmetry: agreement everywhere makes the migration mechanical and platinum cheaper to price, disagreement is a finding on the scale of the two-families work and arrives before a seam locks anything in. Either answer outvalues the harness. Scope and cost: `docs/maintenance/EVALUATOR_DIFFERENTIAL_HARNESS_SCOPE_V1.md`. **Standing caveat, recorded so it can be enforced:** a seam WITHOUT the harness is speculative generality -- an abstraction carried for a future that never arrives, which is its own defect. If the harness slips indefinitely, the honest verdict is that the point solution should have been taken |
| R23 | **How to put decisions to the owner (owner instruction, 2026-07-29).** Two standing rules. **(1) Present GOOD / BETTER / BEST**, a quality ladder with each rung priced, not flat alternatives with the recommendation buried in prose. The owner is choosing a tier, not decoding an essay. **(2) WE ALWAYS GO GOLD UNLESS THE COST IS PLATINUM.** High quality is the DEFAULT, not a thing to be re-justified each time; stop asking the owner to re-authorize doing it properly. The only thing worth escalating is when a rung's cost is disproportionate -- and then say so plainly, with the evidence that makes it platinum (a benchmark, a blast radius, a governance burden that never ends). Corollary: an option must not be dressed as "good" when this lane's own evidence says it is defective -- if a rung reintroduces a known defect class, it is not a rung, it is a warning |
| R21a | **Survey correction, owner-supplied 2026-07-29: `join_engine.cpp` exists, and it does NOT contain a join algorithm.** My P4 survey read `cmd_relations.cpp` and missed `src/cli/join_engine.cpp` entirely; the owner supplied the full chain (`shell_commands.cpp:307` -> `cmd_rel.cpp:132` -> `cmd_relations.cpp:653` -> `join_engine.cpp` -> HELP at `helpdata_messages.cpp:2031`). Reading it: 3.6 KB, `layer: helper`, and its own header states that after "the true join enumerator change, REL JOIN delegates to `relations_api::enum_emit_for_current_parent()` (same behavior as REL ENUM)", with the legacy single-current-row form preserved as `REL JOIN ONE` via `join_emit_one_for_current_parent()`. It also carries a `WorkAreaCursorRestore` guard. So it is a DELEGATION HOOK plus cursor restoration, not set matching. **This CONFIRMS R21 rather than overturning it:** there is no set-matching machinery to reuse, so P4 must still build its own, and the estimate stands. Full grammar, which is richer than the charter recorded: `REL JOIN [ONE] [DISTINCT\|ALL] [LIMIT <n>] [<child-chain>...] TUPLE <fields>`. Worth noting for its own sake: a file named `join_engine.cpp` that contains no join engine is the same name-versus-reality gap this lane logged seven times on 2026-07-29 |
| R21b | **Two registration gaps found alongside R21a, both the class this lane keeps closing.** (1) `REGRESSION RELJOIN` is registered in the curated catalog (`cmd_regression.cpp:134`) and points at `main\rel_join_enum_regression.dts` -- a 12-test suite that is **UNTRACKED**. A fresh clone can list the regression and cannot run it, which is a documented-not-honoured failure at the fixture layer rather than the contract layer. Promote or the catalog entry is a promise the repo cannot keep. (2) A bare `JOIN` sits in `fox_standard_catalog.cpp:3122` with **no `registry().add("JOIN")` anywhere** -- catalog-only, no runnable command. Owner assessment is stale historical evidence; either way it is a phantom, and `shortcut_target_gate.py`'s sibling check (does every catalogued name resolve to a registered command?) would have caught it |
| R21 | **P4 joins take their own set-matching path (owner ruling on OQ-4, option B, 2026-07-29).** `SELECT ... JOIN ... ON a.x = b.y` matches any two columns AD HOC -- no `REL ADD` required, no declared relation consulted. Inner side is index-assisted via `CdxBackend::seek` when the ON key has a usable tag, falling back to a scan, and the chosen access path is REPORTED on every join exactly as ORDER BY reports its own (silent degradation is forbidden). This keeps the two relational methodologies distinct as R17 requires and as the corrected website now states: REL is DECLARED TRAVERSAL along configured paths, SQLsel JOIN is SET MATCHING on arbitrary keys. Option C (hybrid: use REL when one happens to exist) was rejected on this lane's own evidence -- every buffer-visibility defect found on 2026-07-29 lived at a seam where two paths answered one question differently. Consequence: the join's inner-side lookup IS the first production `seek()` consumer, so P1.5 is absorbed into P4 rather than done separately |
| R22 | **LEFT JOIN ships with an explicit unmatched marker (owner ruling on OQ-5, 2026-07-29).** x64base has no NULL (R16 closed OQ-2: blank is a value), so unmatched right-side columns must NOT render as blanks -- that would be indistinguishable from genuine blank data. They render with a distinct marker instead. The owner accepted the stated cost: this INVENTS A DISPLAY CONVENTION that every other tuple-rendering surface will eventually have to honor, so the marker is defined once, in one place, and referenced -- never re-spelled per surface. Safety does not rest on the marker alone: every LEFT JOIN also REPORTS how many rows were left-extended, so the count is visible even if a rendered value looks ambiguous. Oracle regressions map SQLite NULL to the marker explicitly, which documents the equivalence rather than hiding it |
| OQ-4 | **RULED -- see R21.** Original text kept because the survey finding behind it is the reusable part: | Survey finding (2026-07-29): the engine ALREADY produces join-shaped rows. `REL JOIN <path> TUPLE <expr>` walks the declared relation graph and emits one row per leaf combination -- observed live, one STUDENTS row expanding to 7 rows across `enroll -> classes -> tassign -> teachers`. What is missing is not the ability to combine tables; it is SQL syntax and AD-HOC key matching (SQL joins any two columns on demand; REL follows paths declared in advance by `REL ADD`). Three ways to build `SELECT ... JOIN ... ON`: **(A)** compile it down to declared traversal -- cheapest, reuses proven machinery, but a user must `REL ADD` before joining, which no SQL user expects, and it blurs the two methodologies R17 requires be reported distinctly; **(B)** its own set-matching path, index-assisted on the inner side via `CdxBackend::seek` -- honest SQL semantics, ad-hoc keys, no pre-declaration, keeps REL as declared traversal and SQLsel JOIN as set matching, and its inner-side lookup is the natural first production `seek()` consumer already scheduled as P1.5; **(C)** hybrid -- use a declared relation when one happens to exist, else fall back. **(C) is recommended AGAINST on this lane's own evidence:** every buffer-visibility defect found today lived at exactly such a seam, where two paths answered the same question differently, and a join that silently changes strategy could return different row counts for the same query depending on session state |
| OQ-5 | **RULED -- see R22.** Original statement of the problem kept: | R16 closed OQ-2 as blank-is-a-value: x64base has no NULL. SQL LEFT JOIN fills unmatched right-side columns with NULL, so a literal implementation would emit blanks INDISTINGUISHABLE from genuine blank data -- a wrong answer that looks like an answer, the exact defect class this lane closed three times. Options: INNER-only in the first slice with LEFT deferred until unmatched representation is ruled; or define a distinct unmatched marker and report it. Recommendation: INNER first |
| R20 | **`SQLSEL` contract flipped `experimental` -> `supported`** (2026-07-29), the act that publishes the surface. Earned by: G3 closed on an in-run SQLite oracle; regression authored AND registered (`SQLSEL_SELECT_V1`, curated catalog); statement semantics frozen per R16b (names its own table, ignores session filter and cursor state, restores every cursor, reads committed truth per R18); every failure path corrective rather than silent. Flipped in three places at once -- the `@dottalk.usage` contract in `cmd_sql_select.cpp` and the `@dottalk.file` headers of `sqlsel_statement.{hpp,cpp}` -- because a surface that is supported in one header and experimental in another is exactly the between-files disagreement this lane spent the day finding. NOT yet supported and still absent from the grammar: joins, GROUP BY, expression projection, DML, the SQL-mode `SELECT` alias |
| R19 | **Product name: `SQLsel`** (owner, 2026-07-29). Capital SQL, lowercase sel. The last open P6 question is closed -- no new name, no "SQLTalk"; the working name IS the product name. `SQLSEL` remains the CLI verb as typed (commands render uppercase by convention); `SQLsel` is the product/brand form for manuals, HELP prose, website, and curriculum. Use the brand form in prose and the verb form in syntax |
| R18 | **TABLE BUFFER visibility split** (AIF-074 follow-up, 2026-07-29): `TUP`/`TUPLE` are preview surfaces and may overlay uncommitted TABLE BUFFER edits; `SQLSEL SELECT` is statement-scoped and reads committed table truth until SQLSEL DML is promoted. Projection and WHERE for one SQLSEL statement must observe the same committed source. |

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
6. **NULL-readiness seams (R29).** Mark every seam with a greppable `NULL-READY:` comment
   (`// NULL-READY:` in C++, `&& NULL-READY:` in DotTalk) so ONE grep produces the platinum
   work list instead of an archaeology exercise. Six seams, all cost-free today:
   a. **Predicate results are an ENUM, never `bool`.** The P4.0b evaluator seam returns
      `{TRUE, FALSE, ERROR}` so `UNKNOWN` is an added enumerator, not a signature change
      rippling through every caller. EVALDIFF already reports T/F/E, so the tri-state shape
      is proven in the harness before it is needed in the engine.
   b. **Cell carriers keep a kind tag** even while exactly one kind is legal, so a NULL kind
      is an added enumerator rather than a type change in `TupleRow`.
   c. **Aggregate accumulators track rows-seen and values-seen SEPARATELY.** R28's reporting
      requirement already forces both counters, so the bookkeeping NULL would need arrives
      free and proven.
   d. **One absent-rendering function.** R22's unmatched marker and any future NULL are
      DISTINCT CONCEPTS (produced-absent vs stored-absent) that render through a SINGLE
      routine, so NULL cannot introduce a second display convention.
   e. **Schema vocabulary reserves nullability** in the DDL/dtschema path even while only
      `NOT NULL` is accepted, so schemas authored now need no rewrite. Coordinate with
      `DDL_SCHEMA_PDLC_LANE_V1.md`.
   f. **Ordering decision points are marked, not ruled.** Every ORDER BY and index site
      carries a `NULL-READY:` note for the future NULLS FIRST/LAST choice, so the platinum
      lane finds the sites rather than hunting them.

## 4. Phase register (summary; the plan of record carries the detail)

| Phase | One line | Gate |
|---|---|---|
| P0 | Demote phantom SQL contracts (8 files, `supported` -> `experimental`); consolidate 5 duplicated helpers; resolve `cli::AliasRegistry`; run the AIF-073 harness | G0 |
| P1 | Engine seams: PRIMARY/UNIQUE metadata (4 consumers), TupleRow type surface + null ruling (OQ-2), truncation honesty (RDB-06), typed equality, first production `seek()` consumer (+PS-01 gate), P1.6 route projection/print expression terms through expr (R12; until it lands, SQLSEL v1 projection is bare columns only with corrective errors) | G1 |
| P2 | `src/sqlsel/` library target; `SET MODE`; `SELECT` router; R8 block; expression-fallback interception | G2 (`SQLMODE_SMOKE`) |
| P4.0a | **IMPLEMENTED 2026-07-30; parity RED (R24c).** Permanent `EVALDIFF` observer + typed, self-erasing SANDBOX fixture + registered explicit-run corpus. Build and real-runtime run completed; cursor restored and fixture erased. Refined result: 20 predicates produced 10 `VERDICT-PARITY`, 2 `PARITY-ON-FAILURE`, and 8 `DIFFERENCES` summaries. The differing predicates reduce to TWO root-cause clusters, not six function defects: the TupleRow AST route does not parse function calls or require end-of-input (ED-01), and classic `EMPTY()` loses its logical type during expansion (ED-02). `DELETED()`, unknown-field, and incompatible-type probes are shared wrong answers proving parity is not correctness. Full result and disposition: `docs/maintenance/EVALUATOR_DIFFERENTIAL_HARNESS_SCOPE_V1.md`; transcript: `labtalk/proofs/runs/20260730_evaldiff_p4_0a.txt`. Observer only; no evaluator semantics changed | G4.0a HARNESS CLOSED / PARITY RED (registered `EVALDIFF`; findings block migration) |
| P4.0b | **BLOCKED BY P4.0a FINDINGS. Evaluator seam + SQLsel migration (R24a/R24b).** One predicate-evaluation interface, two implementations; SQLsel's `WHERE` takes the tuple-bound one with `overlay_table_buffer=false` to preserve R18. Before migration, repair ED-01 and ED-02, then convert the shared `DELETED()` / unknown-field / incompatible-type wrong answers into reported failures under explicit oracle cases. A parity label alone never blesses correctness | G3 RE-RUN unchanged after parity and oracle repair -- if the SQLite oracle still matches row-for-row, the migration changed nothing |
| P4.1 | INNER JOIN, two tables, one equi-key. Adds table ALIASES (`FROM STUDENTS S`) and QUALIFIED column names (`S.LNAME`), which every later slice needs. Nested loop, inner side SCANNED -- correctness before speed | G4a (SQLite oracle, incl. row multiplication) |
| P4.2 | Index-assisted inner side via `CdxBackend::seek` when the ON key has a usable tag; scan fallback; access path REPORTED every time (R21). Absorbs P1.5 | G4b (same oracle results, both paths, plus the path report asserted) |
| P4.3 | LEFT JOIN with the R22 unmatched marker, defined ONCE, plus a left-extended row count on every LEFT JOIN | G4c (oracle with SQLite NULL mapped explicitly to the marker) |
| P4.4 | **RIGHT, FULL, CROSS (R26).** RIGHT = LEFT with operands swapped; FULL = LEFT plus right-side rows that never matched; CROSS = join with no ON. All reuse the ONE R22 marker and the same extended-row count -- no second convention | G4d (oracle across all four outer forms, SQLite NULL mapped to the marker) |
| P4.5 | **DISTINCT and set operations (R26).** UNION / UNION ALL / INTERSECT / EXCEPT. Duplicate elimination and operand column-compatibility both reuse the ONE R16 ordering/equality model already shared by relation equality and ORDER BY -- a second comparison rule invented here is a defect. Blocked on OQ-11 | G4e (oracle, incl. duplicate counts which are where set operations actually go wrong) |
| P4.6 | **GROUP BY / HAVING and the aggregates (R26).** COUNT, SUM, AVG, MIN, MAX. Aggregates run over SQLsel-produced rows, never delegated to native COUNT FOR (which carries session-filter semantics SQLsel ignores) and never to a DbArea command, since a joined row has no DbArea. Blocked on OQ-10 | G4f (oracle, with the OQ-10 blank rule asserted explicitly row-by-row, not just on the totals) |
| P4.7 | **Subqueries (R26).** Scalar, IN, EXISTS; UNCORRELATED first (evaluate once, reuse), CORRELATED second (re-evaluate per outer row). Requires the binder from P4.0b to resolve an inner reference to an outer table. Relational DIVISION becomes expressible here as NOT EXISTS over NOT EXISTS -- documented as a worked example, given no operator. Blocked on OQ-12 | G4g (oracle, incl. a correlated case whose inner result CHANGES per outer row -- an uncorrelated-only implementation passes a badly chosen fixture) |
| P3 | **DONE 2026-07-29.** Single-table `SELECT` (projection/WHERE/ORDER BY/LIMIT/COUNT(*)) | **G3 CLOSED** (SQLite oracle, registered `SQLSEL_SELECT_V1`) |
| P4 | Relational algebra (roll-up of P4.0a-P4.7, R26): join family, set operations, grouping/aggregation, subqueries. Ad-hoc ON matching per R21 -- NO declared relation required (R27); chain nested-loop; index-nested-loop where a tag exists; minimal EXPLAIN | G4 (oracle + cross-algorithm identity) |
| P5 | DML + transactions as assembly: buffer/WAL, FLOCK, delta-based affected-rows, BEGIN/COMMIT/ROLLBACK verbs; `DELETE` alias (R9) | G5 (crash regression + oracle) |
| P6 | PDLC ascent: manual family, HELP, website promotion (closes OQ-9), LabTalk lessons, evidence gallery | G6 (nine-gate checkpoint) |

Out of scope, each returning as its own lane: window functions, common table
expressions, recursive queries, x32 support, any second SQL dialect surface.
The algebra itself is IN scope in full (R26).

## 5. Open rulings, placed where they block

| Ruling needed | Blocks | Proposed default |
|---|---|---|
| OQ-2 blank-vs-NULL | P1.2 (outer joins UNBLOCKED by R22) | blank-is-a-value, documented; no NULL literal in v1 |
| OQ-10 aggregates over blank | **RULED -- see R28 (skip and report) and R29 (NULL-readiness).** Original question kept: SQL skips NULL in SUM/AVG/COUNT(col); x64base has no NULL and R16 ruled blank IS a value, so does AVG over a column containing blanks divide by 200 or by 160? Both defensible, and they differ on real data | P4.6 -- UNBLOCKED |
| OQ-11 set-operation operands | P4.5 | UNION requires operands with compatible column counts and types. DBF types are not SQL types (C/N/D/L/M), so compatibility needs a stated rule. Proposed default: same column COUNT required; per-column comparison follows the R16 model; a type pairing with no R16 ordering is REPORTED and refused rather than coerced |
| OQ-12 correlated subquery cost | P4.7 | A correlated subquery re-runs per outer row, so a 200-row outer over a 200-row inner is 40,000 evaluations. Proposed default: implement it correctly and REPORT the evaluation count every time, the same way P4.2 reports its access path; optimize only against a measured Pinocchio-scale case, never speculatively |
| OQ-13 qualifier namespace DEPTH | **P4.1 -- and it expires there.** | **Cross-lane, owed from AIF-078** (`docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md`). P4.1 is scheduled to add table ALIASES and QUALIFIED column names, "which every later slice needs". That qualifier's namespace is ONE level (table alias) or TWO (workspace + table alias), and the decision is free while the grammar is unwritten. Measured asymmetry: ~3 surfaces if ruled before P4.1 authors it, ~10 surfaces PLUS re-running every closed G4a-G4g oracle gate if retrofitted after P4.7. Per R23, priced as a ladder. **GOOD -- one level.** Table alias only; no workspace concept enters SQLsel. Cost: zero now, and forecloses nothing that a later rewrite could not reopen at the ~10-surface price. **BETTER (recommended) -- two levels, outer reserved and unreachable.** The qualifier grammar admits an outer level that always defaults to the current workspace and has no surface syntax in P4.1. Cost: a sigil reserved in the grammar (`@`; `#n` and `$v` are taken, `@` is absent from `TokKind` and has no `@ row,col SAY` surface -- searched and absent) plus a one-sentence R27 scope clause. Buys the option; builds no feature. **BEST -- two levels, addressable.** `FROM @MCC.STUDENTS S` resolves. Cost: requires a workspace runtime that does not exist and that AIF-070 owns, so this rung is NOT SQLsel's to price and is recorded only to show the ladder's top. **Load-bearing dependency: R27 needs a scope clause either way.** "Any two OPEN tables join with no registry lookup" is unambiguous at one workspace; at several with no scope, every join site inherits `find_open_area_by_name_ci`'s silent first-match (`src/cli/workarea_util.cpp:29-51`), and a mis-resolved join returns plausible WRONG ROWS rather than an error -- the defect class this lane has closed repeatedly. Proposed clause: *open means open WITHIN THE CURRENT WORKSPACE; the qualifier's outer level is reserved and defaults to it.* Related: AIF-078 Q8 proposes NO implicit ancestor walk if depth is ever resolved |
| SET FILTER stance for SQL statements | P3 gate | statements ignore session filter; stated in contract |
| Bare `SQL` command disposition | P2.4 | retire after P0 demotion |
| Product name (SQLTalk?) | P6 | owner's call |
| OQ-14 verb redundancy: why `SQLSEL SELECT`? | grammar surface + docs-wide | **Drop the redundant inner `SELECT`.** `SQLSEL` IS the select verb (the home SQL brand); `SQLSEL SELECT <list> FROM` starts a statement with two select verbs. We never write `foxpro select` or `sqlite select` -- a dialect names its verb once -- so `sqlsel select` is redundant and half-undoes the confusion SQLSEL was coined to remove. Canonical becomes `SQLSEL <select-list> FROM <table> [WHERE][ORDER BY][LIMIT]`. Source: `src/cli/sqlsel_statement.cpp:150` requires the inner `SELECT`, USAGE at `:132-135` documents it. Owner leans clean break (no live scripts depend on it) vs a one-release optional-keyword soft landing. Doc-wide consequence: everywhere, differentiate xBase `SELECT <area>` (`cmd_select.cpp`, work-area switch) from `SQLSEL` (SQL query). Full note: `SQLSEL_VERB_REDUNDANCY_DESIGN_NOTE_V1.md` |

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
