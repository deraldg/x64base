# DOTSCRIPT-ARRAYS — implementation lane (v1)

Status: **proposed / not started** (dev). Arrays are **PLANNED** — not implemented.
Owning lifecycle: DotTalk++ SDLC · DotScript language + expression runtime.
Parent project: `project.x64base.dotscript` (promoted per AIF-040).
Design authority: `docs/maintenance/DOTSCRIPT_ARRAYS_SPEC_V1.md` (DOTSCRIPT-ARRAYS-SPEC-V1).
Source review: `outputs/DOTSCRIPT_ARRAYS_SPEC_REVIEW_2026-07-20.md`.
Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-038).

## What this lane is

Arrays are the **first general-purpose composite runtime value** in DotScript:
one-based, heterogeneous, mutable, xBase-compatible reference semantics, created by
brace literals / `ARRAY()` / `DIMENSION` / `DECLARE`, with native DotTalk++
diagnostics (`ARRAY INFO/LIST/VALIDATE/STATS/LIMITS/TRACE`) and tuple/JSON bridges.
The full normative design is the spec doc; this lane is the **buildable plan**, and
it front-loads the reconciliation the source review found necessary.

## Honest starting truth (source-verified)

- No `A*` functions, no `ARRAY`/`DIMENSION`/`DECLARE` command exist in `src` today.
- `dotref.hpp` / `foxref.hpp` roles match the spec's provenance model.
- `FORMULA`, `LEN`, `EMPTY` are real; the comment lexer is now a single module
  (AIF-037) — the right place to check the brace/`{` tokenization interplay.

## Phase 0 — reconcile with the real runtime (BLOCKS Phase 1)

The spec is normative design, but three foundations must be settled against the
actual engine *before* any Phase-1 code, or the acceptance scripts can't run and the
value integration won't match. These are the review's H1–H3 + M-items:

1. **Variable convention — two distinct mechanisms, not two variable types
   (DECIDED 2026-07-20).** The maintainer's design question — "do we need both types of
   vars, persistent-to-scope and macro variables?" — resolves the sigil question. There
   are not two *kinds of variable*; there is one **value store** plus one **substitution
   operator**:
   - **Scoped memory variables** — a store holding typed *values* (incl. `ArrayRef`),
     with `LOCAL`/`PUBLIC` (later `PRIVATE`/`STATIC`) lifetime. This is what `VAR` stubs
     toward (`src/cli/cmd_var.cpp` — `// TODO: real variable storage/evaluation path`;
     no `$`/memvar storage in `shell_var_utils.cpp`). **Arrays require only this** — `$A`
     holds an `ArrayRef`; you reference an array as a value, never as text.
   - **Macro substitution (`&name`)** — runtime *text* substitution / late binding
     (`field="LNAME"; ? &field` → `? LNAME`). Not storage; an operator that acts on a
     memvar's textual contents. The engine **already reserves single `&`** for this: the
     AIF-037 comment lexer deliberately preserves a lone `&` while treating `&&` as an
     inline comment. Macro substitution is a **separate operator lane** under
     `project.x64base.dotscript`, decoupled from arrays — you never macro-substitute a
     composite value.

   Sigil map (no overlap): `$name` = value reference (memvar), `&name` = macro/text
   substitution, bare `NAME` = field in the current work area. The array lane's variable
   prerequisite is therefore **only** the scoped `$name → Value` store; macro `&` is out
   of scope here. The spec's `$A`/`$I`/`$NAMES` surface stands as-is. (The prior
   "`$` = non-DotScript PowerShell" canary note referred to a stray `$py12=` tail, not a
   language decision — superseded by this record and the qualified-reference model.)
   **Gate satisfied for arrays:** the sigil is confirmed; the scoped memvar runtime is
   the remaining M1b build dependency, tracked below.
2. **Canonical value model.** The spec proposes one `std::variant<Nil, bool, int64,
   double, string, Date, DateTime, MemoRef, Tuple, ArrayRef>`. Reality
   (`src/xexpr/expr_value.cpp`): a **tagged** `xexpr::Value` with
   `ValueKind{None,Bool,Number,String,Date,Error}` — `double`-only numbers, `Date` as
   int32 YYYYMMDD, **no** DateTime/Memo/Tuple value kinds — **plus a second value
   type** `dottalk::expr::EvalValue` (`K_Number`/`K_String`) on the eval path. Decide
   the canonical `Value`, add `ValueKind::Array` + an `ArrayRef` payload there, and
   record how the two value types reconcile. The spec's §31 (one shared array API) and
   §35 (one generalized lvalue) are **required** here, per AIF-037. **Decided
   2026-07-20:** the array *graph mechanics* are proven self-contained in M1a (a
   local §30 `Value` variant), so the mechanics are settled before the value-model wiring;
   M1b extends the tagged `xexpr::Value` with `ValueKind::Array` and maps the leaves — the
   mechanics do not change. This de-risks the reconciliation to a pure binding task.
   **Char cross-compatibility constraint (maintainer, 2026-07-20):** xBase-family
   programs interoperate at the **character** level — values cross program boundaries
   as chars — and the engine's canonical number is `double` (`xexpr::Value` /
   `EvalValue`), serialized locale-free (AIF-031). The array leaf therefore carries
   **no distinct integer kind** (a `std::int64_t` element would not survive a string
   round-trip); numbers are `double` only, and the memvar↔evaluator bridge must go
   through the char/string `ScalarValue` contract, not a private binary path.
   **Canonical Value DECIDED + signed off 2026-07-20:** the canonical domain value is
   `dottalk::value::Value` (DTV) under a two-tier model — DTV is exact/stateful truth,
   the engine's `double` value is its evaluation projection. The array runtime's
   `dottalk::array::Value` is a strict subset with adapters; **the live `ArrayValue`
   must gain a `generation` field** for the ArrayReference registry bridge. See
   `docs/maintenance/tuple_pdlc/CANONICAL_DOTTALK_VALUE_DECISION_ACCEPTED_2026-07-20.md`.
3. **Assumed facilities that don't exist.** `ASSERT`, `VALTYPE`/type inspection,
   `NIL`/`ISNIL` are used throughout the spec and acceptance scripts but are absent.
   Either add them (a small Phase-0 sub-task) **or** rewrite the acceptance scripts in
   the project's real proof idiom (REGRESSION + teed transcript). `ISARRAY`/`ASAME`
   are correctly slated as native to add.
4. **Brace audit (spec §7).** Confirm `{` has no conflicting DotScript meaning today,
   and reserve `{|` (future code block) and `{^` (date literal). The AIF-037 lexer
   module is the single place this interacts with comment tokenization.

Deliverable: a short Phase-0 decision record answering 1–4 with source citations,
before M1.

## Milestones (map the spec's phases + apply the codex)

- **M1a — Provable array core** (spec Phase 1 mechanics). ✅ **DONE + unit-proven
  2026-07-20.** `src/xexpr/array_value.{hpp,cpp}`: the central array API (§31) with the
  single checked-offset helper (§32, the only place that subtracts one), `ArrayValue`/
  `ArrayRef` (shared_ptr) with object ids + mutation/structure sequences, `create_empty/
  sized/nested`, `length` (ALEN), `is_array` (ISARRAY), `get`/`set` (one-based,
  no implicit resize), `add` (AADD), `resize` (ASIZE, grow-with-NIL), `clone_deep`
  (ACLONE, topology-preserving — a child shared twice is cloned once, not duplicated),
  `same_object` (ASAME), `equal_structural` (cycle-safe visited-pair `==`), and
  `would_create_cycle` (direct + indirect rejection). The element leaf is the spec §30
  conceptual `Value` kept **self-contained** so the graph mechanics — where the real
  bugs live — are compiled + unit-proven with g++ independent of the engine, exactly
  like the AIF-037 lexer module. Proof: `g++ -std=c++17` build clean, all assertions
  pass (reference sharing across aliases; ACLONE independence + shared-child topology;
  one-based bounds + zero/over-range rejection; no-implicit-resize; ASIZE NIL-fill;
  NIL ≠ empty-array ≠ empty-string; ordered structural equality; direct + indirect
  cycle rejection; independent nested children). No engine build required; nothing
  wired into the runtime yet.
- **M1b-1 — Value-model binding.** ✅ **DONE, MSVC-green 2026-07-20.** Extended the
  canonical `xexpr::Value` with `ValueKind::Array` + a forward-declared `ArrayRef`
  payload, `Value::array()`/`is_array()`/`as_array()`, and `Array` cases in
  `truthy`/`display` (`{array:N}`); added `array_value.cpp` to the `xexpr` library.
  Additive only — nothing in the eval path constructs an Array yet, so existing tests
  stayed green. All three `ValueKind` consumer switches carry a `default`.
- **M1b-2a — Scoped memvar store.** ✅ **DONE + g++-proven 2026-07-20**, added to the
  `xexpr` library (`src/xexpr/var_store.{hpp,cpp}`, `dottalk::dotscript::VarStore` +
  `session_vars()`). The Phase-0 §1 prerequisite, built greenfield and self-contained:
  case-insensitive `$name` bindings storing the reused `dottalk::array::Value` (scalars
  *or* `ArrayRef`), a PUBLIC/global frame 0 plus a scope stack (LOCAL shadows PUBLIC,
  discarded on pop; frame 0 never pops), `assign`/`get`/`release`/`clear`. Proof:
  scalar + array store/get, **array reference identity preserved** (mutation through a
  retrieved handle is visible via the store), overwrite, release, scope shadow/discard.
  PRIVATE dynamic hiding + STATIC persistence deferred (honest first cut).
- **M1b-2b — Scalar memvars end-to-end.** ✅ **DONE, MSVC-green + REPL-proven
  2026-07-20** (`VAR threshold = 3.0` then `? $threshold * 2` → `6`; `VAR label =
  UPPER('hi')` → `$label` → `HI`; `VAR n = 40 + 2` → `$n` → `42`). (a) headers promoted
  to `include/xexpr/` (public) so CLI TUs can include them;
  (b) `ValueParser::parse_primary` resolves a `$name` reference from `session_vars()`
  right before the string-literal degradation (rhs_eval.cpp) — the `$` sigil is
  unambiguous so this is additive and cannot shadow a field; (c) `cmd_VAR` now evaluates
  its RHS via `eval_rhs` and stores the result under the sigil-stripped, case-insensitive
  name (bool/number/string/date→number; NIL otherwise). An array-valued `$name` renders
  as a `{array:N}` placeholder in scalar expression context until M1b-3. Proof: the exact
  variant/lookup/convert patterns g++-verified in isolation; full REPL proof on build.
- **M1b-2c — Array literals + subscripts.** ✅ **DONE, MSVC-green + REPL-proven
  2026-07-20** (`VAR a = {10,20,30}` then `? $a[2]` → `20`; `? $a[2]+5` → `25`;
  `VAR m = {1,{2,3}}` → `? $m[2][1]` → `2`; `? $a` → `{array:3}`). Extended the scalar
  lexer `Tok`/`lex_value_expr` for `{` `}` `[` `]`; `ScalarValue` gained a `K_Array`
  kind carrying an `ArrayRef` (+ `sv_to_avalue`/`avalue_to_sv` bridges); `parse_primary`
  builds `{…}` literals through the central array API; a new `parse_postfix` applies
  chainable one-based `$A[n]` subscripts. **Bug found + fixed via the build (not the
  sandbox):** `VAR` originally stored through `eval_rhs`, whose `EvalValue` has no array
  kind, so `{1,2,3}` was flattened to the string `"{array:3}"` and `$a[n]` had nothing
  to subscript. Added an array-preserving evaluator entry `eval_rhs_avalue`
  (rhs_eval.hpp/.cpp) that returns the array-lane `Value`; `cmd_VAR` now uses it and
  stores the real `ArrayRef`. Brace-reservation for `{|…|}` / `{^…}` still holds (they
  fail cleanly rather than misparsing).
- **M1b-3 — Array functions + errors** (build-required). Register `ALEN`/`AADD`/
  `ASIZE`/`ACLONE`/`ASAME`/`ISARRAY`/`VALTYPE`/`NIL` on that layer; array errors via
  `emit_error` + message-catalog severity (AIF-036). Everything routes through the M1a
  API — no `std::vector<Value>` poked directly (AIF-037). Proof idiom: REGRESSION +
  teed transcript (not the spec's `ASSERT`).
- **M2 — Compatibility functions** (Phase 2). `DIMENSION`/`DECLARE`, `ADEL`, `AINS`,
  `AFILL`, `ASCAN` (value form), `ACOPY`, `ASORT` (default), `ATAIL` — established
  xBase semantics preserved exactly.
- **M3 — Native diagnostics** (Phase 3). `ARRAY INFO/LIST/VALIDATE/STATS/LIMITS/TRACE`
  (dotref lane). Diagnostics before deeper integration, so later work is observable.
- **M4 — Control flow** (Phase 4). `FOR EACH` + iterator structure-change detection;
  optional code-block runtime → `AEVAL`, predicate `ASCAN`, comparator `ASORT`.
- **M5 — Data bridges** (Phase 5). `AFIELDS`, `DBSTRUCT`, tuple bridges,
  bounded `TUPMATERIALIZE`, `JSONENCODE`/`JSONDECODE`, optional `SCATTER`/`GATHER`.

## Cross-lane wiring (reuse, don't reinvent — AIF-037)

- **Errors derive from messaging (AIF-036).** The spec's `ARRAY_*` identifiers become
  message-catalog `MessageId`s with a **facility** (`runtime`) and a **severity**, emitted
  via `emit_error`. `stop_on_error[severity]` then governs whether an array error halts
  a script — the array error catalog is *not* a parallel scheme.
- **Catalog/provenance.** foxref (xBase family) vs dotref (native) classification flows
  through the existing SYSCMD/SYSFUNC + HELP/SelfDoc metadata the website catalogs
  already harvest (AIF-025), not a new metadata store.
- **Manual/website.** New commands/functions surface through the manifest-driven
  manual assembler + catalog generators (AIF-033/035) once they exist.

## Definition of Done (spec §46, kept honest)

Arrays in the ordinary `Value`; literals/`ARRAY()` parse+evaluate; one-based read/write;
nested + comma subscripts; cataloged out-of-range/type errors; assignment shares
identity; `ACLONE` recursive + topology-preserving; Phase-2 compat functions correct;
direct+indirect cycles rejected; limits enforced pre-allocation; native diagnostics
report identity/contents/limits/integrity; arrays work in `$VAR`/expr/functions/loops
(and assertions, once ASSERT/REGRESSION is settled); **no** array responsibility added
to DbArea; tuple/memo boundaries orthogonal; existing scalar/db/index/tuple/memo tests
stay green; every public command/function has HELP+SelfDoc metadata; foxref/dotref
provenance correct; **status truthful and runtime-proven** (PLANNED→PARTIAL→SUPPORTED
only on proof).

## Non-goals / honesty

Not everything ships at once — code blocks (`{|…|}`), `AEVAL`, comparator sort,
`FOR EACH`, cycles-with-GC are deferred by design. Arrays never become a DBF field
type. This lane does not start until Phase 0's four reconciliations are recorded.
Dev-only until built + proven.

## Provenance pointers

- Design authority: `docs/maintenance/DOTSCRIPT_ARRAYS_SPEC_V1.md`;
  machine catalog: the author's `DotScript_Arrays_Catalog_v1.json`.
- Source review (holes): `outputs/DOTSCRIPT_ARRAYS_SPEC_REVIEW_2026-07-20.md`.
- Value model: `src/xexpr/expr_value.cpp`, `src/xexpr/expr_eval.cpp`.
- Standards: AI_PORTAL.md "Representative by Design" (AIF-037); stop_on_error /
  messaging (AIF-036); catalog harvest (AIF-025).
- Reference lanes: `include/dotref.hpp`, `include/foxref.hpp`.
