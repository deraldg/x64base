# DotScript Build Plan V1 -- Functions, Frames, and the Error Probe

Lane: **AIF-109** (DotScript product-gap umbrella). Owner: member.derald.
Coworker of record: member.ai.claude.cowork. Authored 2026-08-12 on owner
instruction: "re-review all of our specs and suggestions and lay out a plan,
design, build, implement flow for dotscript, with appropriate milestones,
modeled for an agnostic planner."

**Agnostic-planner contract.** This document assumes NO session memory, NO
particular AI, and NO conversation context. Any planner -- the owner, a house
coworker session, an external agent through the challenge protocol -- can
execute it from the tree alone. Every claim cites a document or a source
file; every milestone has a falsifiable exit gate; every decision that was
the owner's to make is already made and cited. Where this plan and a cited
source disagree, THE CITED SOURCE WINS and this plan is the artifact to
correct (the transcript-wins rule).

---

## 1. Inputs ledger (the complete review set)

An executor reads these before writing anything. Nothing else is required.

| # | Artifact | Authority |
| --- | --- | --- |
| I1 | `docs/maintenance/DOTSCRIPT_ARRAYS_SPEC_V1.md` | NORMATIVE for the value model, grammar reservations, reference semantics, limits, and the error contract. Sections that bind this lane: s5 (value model; `callable` anticipated), s7 (grammar: `{\|` reserved for code blocks), s11 (reference semantics), s13 (cycle policy), s18 (control flow; FOR EACH deferred), s19 (procedure/function parameters -- arrays pass by reference; local rebinding is local; BINDS ALL FUTURE TYPES), s27 (runtime limits pattern: caps checked BEFORE allocation), s29 (error contract: catalogued, localizable message ids), s30-s37 (runtime representation and central API) |
| I2 | `docs/maintenance/DOTSCRIPT_FUNCTION_SURFACE_PRIOR_ART_V1.md` | The findings note: measured seams, collision hazards, and the FIVE RESOLVED OWNER RULINGS (its section 6) plus governing doctrine. This plan is its execution arm |
| I3 | `docs/maintenance/external_ai_intake/dotscript_control_flow_review_2026-08-12/MANIFEST.md` | Grok peer review (preserved verbatim): control-flow inventory, gap list, and the assessment recording three name collisions |
| I4 | `docs/maintenance/DOTSCRIPT_STOP_ON_ERROR_LANE_V1.md` (AIF-036) | The errorstop lane: threshold semantics, error runtime lineage |
| I5 | `docs/maintenance/DOTSCRIPT_ARRAYS_LANE_V1.md` (AIF-038) | The arrays lane: how a language increment runs under PDLC here |
| I6 | Source of record: `src/cli/cmd_deffn.cpp`, `cmd_defcmd.cpp`, `cmd_dotscript.cpp`, `cmd_loop.cpp`, `cmd_while.cpp`, `cmd_until.cpp`, `cmd_scan.cpp`, `cmd_if.cpp`, `cmd_stop_on_error.cpp`, `cmd_quit.cpp` (EXIT alias), `include/xbase_error_context.hpp`, `include/xexpr/array_value.hpp`, `include/value/value.hpp` | Behavior ground truth. Re-measure before trusting any summary, including this one |
| I7 | `labtalk/registries/projects.yaml` -> `project.x64base.dotscript` | Registry: lanes `functions_procedures` + `error_handling` under AIF-109 |
| I8 | Regressions: `DOTSCRIPT_EXPR`, `DOTSCRIPT_PARITY` (default suite), `LEXING`, `SCAN_PARITY`, `ERRORSTOP` (`src/cli/cmd_regression.cpp`, `kRegressionSpecs`) | The no-blowing-up baseline: all must stay green through every milestone |
| I9 | `AI_README.md` Working Rules + `labtalk/ai_portal/AI_GLOSSARY_V1.md` | House rules that gate the work (see section 3) |

## 2. Decisions already made (do not re-litigate)

All five rulings resolved by the owner 2026-08-12 (I2 section 6), under the
doctrine **"go for gold unless the cost is platinum"** (glossary):

| D | Ruling |
| --- | --- |
| D1 | Parameters on the FUNCTION signature line: `FUNCTION NAME($A, $B)`. Not a PARAMETERS body line |
| D2 | `LOCAL` is explicitly declared; scope is Pascal-style procedure nesting -- a local is visible to the declaring procedure AND its callees; an inner declaration of the same name shadows. (Close kin of classic xBase PRIVATE; pure lexical isolation was NOT chosen) |
| D3 | Function bodies live INLINE in the `.dts` file |
| D4 | Recursion cap: hard 1000 as a NAMED CONSTANT (one edit to change), matching LOOP's max-iterations precedent |
| D5 | Error model: expose error state to expressions and keep the `STOP_ON_ERROR` threshold; `TRY`/`CATCH` deferred (demonstrated-negation candidate). The owner's framing: the policy already IS bypass-vs-hard-stop; make it per-operation scriptable |

Constraints that are settled law, not choices:

- **C1** Arrays (and by s19's own words all future types) pass as REFERENCE
  values; rebinding a parameter changes only the local binding (I1 s19).
- **C2** `{\|` stays reserved for code blocks; the function grammar must not
  spend it (I1 s7).
- **C3** Name collisions (I2 section 1b): `EXIT` is the shell-quit alias,
  `LOOP` opens a counted block, `DO` runs scripts. The function lane
  introduces NO break/continue/case keywords and does not touch these.
- **C4** WHILE/UNTIL are RECORD loops (advance one record per iteration);
  frames live BELOW that policy and must not change it (I2 section 5c).
- **C5** Limits are checked BEFORE allocation and are configurable-by-pattern
  (I1 s27). New error conditions extend the s29 message-id contract -- no
  parallel error vocabulary.
- **C6** One serializer / one truth discipline applies to any new registry or
  format artifact (house rule; see the DTSHEMA collision record).

## 3. House rules that gate every milestone

- **G1 Evidence tiers**: nothing is claimed above its proof. runtime-proven
  needs a transcript with a build stamp; the stamp is part of the proof.
- **G2 Promote-final-tests**: each milestone's proof script is promoted into
  `kRegressionSpecs` the day it goes green -- AND THE ARRAY COUNT IS BUMPED
  (the recurring papercut; the compile error is the safe failure).
- **G3 No-blowing-up baseline**: the I8 regressions run green on the same
  build as every new proof.
- **G4 Coordination**: scoped `git add` by explicit path, never `-A`;
  `status --short` between add and commit; builds and runs are
  maintainer-executed; sandbox sessions never mutate git.
- **G5 Tooling**: Python 3 stdlib or DotScript for any helper; ASCII in all
  house-authored text (`--`, `->`); `* ` / `&&` comments in `.dts`.
- **G6 Talk-before-do**: any point where this plan proves wrong or
  underspecified goes back to the owner as a question, not a guess.

## 4. The flow: Plan -> Design -> Build -> Implement -> Prove -> Document -> Maintain

Each milestone lists: goal, work, exit gate (falsifiable), and evidence.
Milestones are strictly ordered unless marked parallel-safe.

### M0 -- Re-measure and charter (Plan)

Goal: an executor independently confirms the ground truth this plan stands
on, then freezes scope.

Work:
1. Re-measure I6: DEFFN registers via `fn_custom` and resolves in `?`/CALC/
   WHERE; the dispatch depth guard refuses at `g_dotscript_depth >= 2`; the
   block family buffers-and-replays through the named executor; the error
   runtime carries typed last-error + generation counter with NO
   expression-visible probe. (If any measurement differs from I2, STOP --
   correct I2 first, per the transcript-wins rule.)
2. Grammar audit (the s7 precedent): confirm `(` after a command token has
   no conflicting meaning in command position; confirm `$NAME` parsing in an
   argument list context; record findings in the design doc (M1).
3. Freeze scope: THIS lane ships functions/frames + the error probe. It does
   NOT ship CASE, break/continue, counted FOR, FOR EACH, TRY/CATCH,
   codeblocks, or maps (all recorded as deferred with their blockers).

Exit gate: a short M0 findings section appended to the design doc skeleton,
listing each re-measurement with file:line, and the grammar-audit result.
Evidence: the appended section itself; no runtime claim is made at M0.

### M1 -- Normative function-surface spec (Design)

Goal: a sibling of the arrays spec, written BEFORE code, so the language has
one authority per surface.

Work -- author `docs/maintenance/DOTSCRIPT_FUNCTIONS_SPEC_V1.md` covering:
1. Grammar: `FUNCTION <name>([$p1[, $p2 ...]])` ... `ENDFUNC`;
   `PROCEDURE`/`ENDPROC` as the no-return-value twin (or a single keyword --
   the spec decides and says why); `RETURN [expr]`; `LOCAL $name[, ...]`.
   Case-insensitive keywords per house norm. No new tokens beyond `(` `)` in
   the signature position (C2, C3 honored by construction).
2. Semantics: D1-D4 verbatim; call-by-reference per C1 with the s19 rebinding
   rule quoted; name resolution order (locals -> enclosing frames -> globals
   -> fields? -- the spec must rule the ambiguity order explicitly and align
   with the existing memvar/field resolution the parity regressions prove);
   shadowing; what an undeclared assignment inside a frame means (given D2:
   it targets the nearest declared scope, else global -- spec states it).
3. Frame model: the call stack, `kDotScriptMaxCallDepth = 1000` (D4, named
   constant), depth checked BEFORE frame allocation (C5), the buffered-body
   registry (definitions captured by the same buffer-and-replay gesture the
   block family uses; `ENDFUNC` FILES the body instead of executing it).
4. DEFFN/DEFCMD relationship: promotion path from text macros to real bodies
   on the SAME registries (their contracts already declare the MVP limits);
   what remains of the text-macro behavior, if anything.
5. Error contract additions (s29 style): `FUNC_DEPTH`, `FUNC_PARAM_COUNT`,
   `FUNC_UNDEFINED`, `FUNC_REDEFINE_BUILTIN`, `LOCAL_OUTSIDE_FRAME` --
   catalogued, localizable, templated.
6. Diagnostics: a `FUNCTION LIST` / `FUNCTION INFO <name>` family on the s17
   ARRAY-diagnostic pattern (name, arity, body line count, defined-where).
7. Interaction table: with SCAN/LOOP/WHILE/UNTIL (a function may be CALLED
   inside them; defining inside a buffered block is refused in v1 -- stated
   plainly); with `DO <script>` (calls do not consume subscript depth once M4
   lands; until then the existing limit stands); with STOP_ON_ERROR (a
   recorded error inside a frame obeys the same threshold).
8. Explicit non-goals with blockers named (the M0 freeze list).

Exit gate: spec exists, is ASCII-clean, cites I1 sections at each inherited
rule, contains the M0 findings, and its provenance-classification section
follows I1 s3. Owner has seen the two spec-decided items (PROCEDURE twin
yes/no; resolution order) -- these are presentation of consequences, not new
rulings, but G6 says show them.

### M2 -- Core frames (Build)

Goal: the mechanism, smallest correct cut.

Work (suggested slice order, each compiling):
1. Frame runtime: a call-stack structure holding locals (name -> xexpr
   Value), parameter binding (by reference per C1 -- an ArrayRef copy IS the
   shared reference; scalars copy by value semantics of the Value type),
   RETURN value plumbing, and the named depth constant with its BEFORE-
   allocation check.
2. Definition capture: `FUNCTION` begins buffering (the existing gesture);
   `ENDFUNC` validates the signature, files the body + arity into the
   function registry (the `fn_custom`/DEFFN seam), refusing builtin shadowing
   exactly as DEFFN already does.
3. Call path: expression-side invocation `NAME(args...)` resolves through
   the same seam that already resolves DEFFN customs; command-side `NAME
   args` optionally via the DEFCMD seam (spec M1 decides if v1 includes it).
4. `LOCAL` statement: valid only inside a frame (else `LOCAL_OUTSIDE_FRAME`);
   registers names in the current frame.
5. `RETURN`: sets the frame's return value and unwinds to the call site
   through the executor -- NOT via process/script termination.

Exit gate: compiles on the primary toolchain; a hand `.dts` exercising
define/call/return/local runs green in a maintainer-executed session with a
fresh build stamp. No regression promoted yet (that is M3's job).
Evidence: the hand transcript.

### M3 -- Prove and promote (Prove)

Goal: the standing proof, in the house style.

Work: author `dottalkpp/data/scripts/dotscript_functions_regression.dts`
with field-value/`? "F_Tn_...:"` markers covering AT MINIMUM:
- F_T1 define + call + returned value used in an expression
- F_T2 parameter binding positional; F_T3 arity mismatch -> catalogued error
- F_T4 LOCAL shadows an outer name; outer value intact after return
- F_T5 Pascal nesting: callee reads caller's local (D2), inner shadow wins
- F_T6 array parameter mutated in callee is visible to caller (C1/s19);
  rebinding in callee does NOT rebind caller (s19 second clause)
- F_T7 recursion (factorial or similar) correct at modest depth
- F_T8 depth refusal at the cap: clean catalogued error, session healthy after
- F_T9 builtin-shadow refusal
- F_T10 a function called inside SCAN and inside LOOP bodies works

Promote as spec `DOTSCRIPT_FUNC` (bump the array count -- G2), explicit-run
until soaked. Run the I8 baseline on the SAME build.

Exit gate: DOTSCRIPT_FUNC green AND all I8 regressions green, one build
stamp, maintainer transcript. Evidence: the transcript + the spec entry
carrying its doctrine text.

### M4 -- Lift the nesting ceilings (Implement)

Goal: the frame machinery retires the one-subscript limit and the block
family's re-entrancy guards where they exist only for want of frames.

Work:
1. Replace `g_dotscript_depth >= 2` with a frame/script-depth accounting
   under the SAME named-constant discipline (its contract header line
   `nesting_limit:` updated in the same commit -- the self-declared contract
   must not drift from behavior).
2. Revisit SCAN's "nested SCAN not allowed" and the private-buffer twins:
   lift what frames genuinely fix; KEEP what is a deliberate design (C4);
   record each decision in the M1 spec's interaction table.
3. Update affected regression doctrine texts (LEXING/SCAN_PARITY if their
   texts state the old limits) -- the IDXSTALE precedent: the subject moved,
   say so, never silently retune.

Exit gate: a nested-subscript + nested-block hand proof green; full default
suite (`REGRESSION ALL`) green; any spec text that stated old limits updated
in the same slice. Evidence: transcripts + the diff.

### M5 -- Error probe (Implement, parallel-safe after M3)

Goal: D5's ruling -- the smallest surface that makes bypass-vs-stop
scriptable per operation.

Work:
1. Two catalog functions over the EXISTING runtime (I6
   `xbase_error_context.hpp`): an error-state probe (last error code /
   severity / ok-ness) and a generation read -- names per the house function
   naming rules, registered in fn specs AND the SYSFUNC catalog (the
   cross-authority gate reconciles 74/74 today; it must reconcile N/N after,
   in the same slice, or the normalization gate blocks -- that is the gate
   doing its job).
2. Documented pattern in the language guide: `ERROR_CLEAR` -> attempt ->
   probe/compare-generation -> `IF` branch. The scripted poor-man's TRY.
3. Regression `DOTSCRIPT_ERRPROBE`: provoke a recorded error under
   `STOP_ON_ERROR OFF`, branch on the probe, prove the script COMPLETED and
   CHOSE; then prove threshold interplay (WARNING aborts where configured).
4. TRY/CATCH stays deferred: add the demonstrated-negation exhibit to the
   lane record -- the probe pattern covering the enumerated real cases IS the
   evidence the block construct can wait.

Exit gate: DOTSCRIPT_ERRPROBE green; normalization gate PASS with the new
function count; ERRORSTOP regression still green. Evidence: transcripts.

### M6 -- DEFFN/DEFCMD promotion (Implement)

Goal: the experimental text macros become real definitions on the seams they
own, per the M1 spec's promotion section.

Work: DEFFN bodies become expression-evaluated (arguments bound per D1/C1);
DEFCMD bodies become executed command sequences; their `@dottalk.usage`
blocks updated from the MVP wording IN THE SAME COMMIT (the contract and the
behavior move together); `UNDEFFN` semantics preserved.

Exit gate: their usage examples run as documented; DOTSCRIPT_FUNC extended
or a small DEFPROMO regression added; baseline green. Evidence: transcripts.

### M7 -- Document (full-stack)

Goal: the documentation loop closes -- this project's definition of done.

Work (the full-stack doc-push discipline, I9):
1. Language guide: functions chapter (grammar, scope, recursion, the error
   probe pattern), with the go-for-gold note where the surface deliberately
   departs from classic xBase.
2. `dotref.hpp` entries; HELP tables (usage contracts feed them); manuals
   regenerate; localization ids for every new message (s29).
3. Website: `/products/dotscript` gains the function surface with tiers;
   `/docs/engine/specifications` command/function counts refresh from the
   gate; ecosystem comparison rows flip (UDF row: absent -> present with
   evidence); regression index regenerates (34->N entries drift rule).
4. Registry + portal: projects.yaml docs list gains the two new docs;
   AIF-109 row updated ACTIVE -> increments recorded; dashboard Session Log
   row on completion.

Exit gate: matrix rows registered (the blocking closeout gate); site builds
and publishes clean; normalization gate PASS. Evidence: publish transcript +
live URLs.

### M8 -- Maintain and the deferred ledger

Standing state after M7, and what is explicitly NOT built with its blocker:

| Deferred | Blocker / trigger |
| --- | --- |
| FOR EACH | I1 s18: MAY-add after tuple/array dogfood; mutation-guard fields already exist |
| CASE multi-branch | `DO` collision (C3): bare `CASE...ENDCASE` is the candidate form; needs its own mini-spec |
| break / continue | `EXIT`/`LOOP` collisions (C3): needs new words or context-sensitivity; frames make it cheap but naming is an owner call |
| Counted FOR | covered by LOOP n today; revisit with FOR EACH |
| TRY/CATCH | D5: only if the M5 probe pattern is shown insufficient (demonstrated negation pending) |
| Codeblocks `{\|` | grammar reserved (C2); a fresh lane |
| Tuple bridges | I1 s21; TUPTALK is the working half; wants functions returning structured values first |

Maintenance rules: the named depth constant is the only tuning knob; any
future loosening follows strict-then-dynamic; every defect found in the
field becomes a regression before its fix (the canary discipline).

## 5. Dependency graph (for the planner's scheduler)

```
M0 -> M1 -> M2 -> M3 -> M4 -> M6 -> M7
                   \-> M5 (parallel after M3) -> M7
```

M5 may interleave with M4/M6; M7 requires all prior. Estimated shape (not a
promise): M0-M1 one sitting; M2-M3 the long pole; M4-M6 short measured
slices; M7 one full-stack pass.

## 6. Risk register

| Risk | Mitigation |
| --- | --- |
| Parser change destabilizes existing scripts | signature grammar is additive (new context after FUNCTION token only); LEXING + PARITY on every build (G3) |
| Scope model surprises memvar/field resolution | M1 rules the order explicitly against the parity regressions; F_T4/F_T5 pin it |
| Executor unification breaks a block construct | M4 touches guards one at a time, each with a hand proof before the suite |
| Function-count drift trips the normalization gate | the gate is the safety net, not the enemy: fn specs + SYSFUNC move in one slice (M5) |
| Spec-count papercut | G2 names it; the compile error is the designed failure |
| A future planner trusts this plan over the tree | the transcript-wins rule in the header; M0 exists precisely to re-measure |

---

*Everything in this plan was measured or ruled before it was written; the
plan's job is ordering, not invention. If executing it teaches something the
inputs did not know, the inputs get corrected first -- we regroup, go back
and amend, and move forward.*
