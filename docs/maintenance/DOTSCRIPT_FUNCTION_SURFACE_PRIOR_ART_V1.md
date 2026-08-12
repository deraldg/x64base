# DotScript Function Surface -- Prior-Art Findings (V1)

Status: **findings note, not a charter.** No lane is opened and no syntax is
proposed here. This exists because an external AI evaluation (2026-08-11,
Outside-AI instance, public materials only) ranked three DotScript gaps as
critical, and the house rule is prior art before design. The prior art turned
out to be much larger than the gap list implied, and it constrains the answer.

Owner: member.derald. **Coworker of record: member.ai.claude.cowork**
(owner assignment 2026-08-12, "assign yourself the co-worker on those tasks
for the record"). Date: 2026-08-12.

Attribution note, recorded because the distinction is the point: *coworker*
is the house term for an AI agency working as the owner's personal coagent
under house identity and house rules -- not an agent of the model vendor, and
not an autonomous actor. Every measurement in this note was taken read-only;
every mutation to the tree was authored here and executed by the owner. That
division is what makes the attribution meaningful rather than decorative.

Subjects read: `src/cli/cmd_deffn.cpp`, `src/cli/cmd_defcmd.cpp`,
`src/cli/cmd_dotscript.cpp`, `src/cli/cmd_tuptalk.cpp`,
`include/xexpr/array_value.hpp`, `include/value/value.hpp`, and
`docs/maintenance/DOTSCRIPT_ARRAYS_SPEC_V1.md` (37 sections, normative,
2026-08-06, AIF-038).

---

## 1. The external evaluation, checked

| External claim | Verdict against the tree |
| --- | --- |
| User-defined functions/procedures still missing -- Critical | **Correct as a capability claim**, but see section 2: the registration and resolution seams exist and are proven; only the evaluation half is absent |
| Error handling (ON ERROR / TRY) still missing -- High | **Correct.** No `ON ERROR`, `TRY`, or `CATCH` anywhere in the command surface. `STOP_ON_ERROR` is a threshold policy (continue vs abort), a different mechanism |
| Variable scoping (LOCAL) still global-centric -- High | **Correct**, and coupled to the function gap: locals without call frames have nothing to be local to |
| Script composition / multi-level nesting -- High | **Correct and precisely bounded**: `g_dotscript_depth >= 2` refuses with "nesting limit reached (max 1 subscript)", and the command's own contract header already declares `nesting_limit: main plus one subscript` |
| Arrays live -- closed | **Correct**, and far deeper than "arrays": a specified value model with reference semantics, cycle policy, and limits |
| Line continuation -- closed | **Correct** |

The evaluation was produced from public materials and matches the tree on
every point. That accuracy is itself a data point for the AIF-108 cooperation
experiment chartered the previous night.

## 1b. Peer review: control flow (Grok, 2026-08-12)

A second outside evaluation arrived the day after the first -- an xBase
control-flow inventory versus the DotScript surface, **authored by
member.ai.grok.xai and designated a peer review by the owner**. Verbatim
text preserved at
`docs/maintenance/external_ai_intake/dotscript_control_flow_review_2026-08-12/MANIFEST.md`.
Same agency as the open Lane 1 assignment and the reserved AIF-102 -- Grok
active in the peer-review role while that assignment stays open. Checked
against the tree:
**accurate on every presence/absence claim** -- IF/ELSE/ENDIF, LOOP n,
WHILE/ENDWHILE, UNTIL/ENDUNTIL, SCAN/ENDSCAN present; DO CASE, loop
EXIT/LOOP (break/continue), counted FOR, and FOR EACH absent; the
single-buffered-SCAN limit real. Its design judgments also hold: SCAN as the
first-class construct is the right priority for a database language, and
explicit UNTIL beats the classic infinite-WHILE-plus-EXIT idiom for
teaching.

What outside analysis could not see, and cross-reading against the tree
adds -- **three name-collision hazards for the "completeness items" it
recommends**:

1. **`EXIT` is taken -- it quits the shell.** `cmd_quit.cpp` declares
   `aliases: EXIT` ("QUIT and EXIT share the same implementation"), and the
   registry binds `EXIT` to `cmd_QUIT`. A classic loop-`EXIT` (break) would
   collide with a session-terminating command -- the worst possible
   collision, since the failure mode is a script killing the shell.
   Any break keyword needs either context-sensitivity inside buffered
   bodies or a different word.
2. **`LOOP` is taken -- it opens a block.** Classic xBase `LOOP` means
   *continue*; DotScript's `LOOP` *begins* a counted block. A continue
   keyword must be something else (or context-resolved), and the manuals
   should teach the divergence from classic explicitly.
3. **`DO` is taken -- it runs scripts.** `DO mem`, `DO x64`,
   `DO <script>` is the script invocation form, so classic `DO CASE` would
   sit inside the script-runner's parse. A DotScript-faithful multi-way
   branch is more plausibly bare `CASE ... OTHERWISE ... ENDCASE` --
   period-adjacent, collision-free, same end-keyword style.

Two nuances the evaluation missed, both already measured in 5c: WHILE and
UNTIL are *record* loops (advance one record per iteration), not general
conditional loops -- a general loop form is a real gap its inventory did not
name; and `LOOP FOR <label>` already exists as an honestly-declared stub.

On FOR EACH, the evaluation's sequencing instinct ("natural once the
tuple-as-array work finishes") is already normative: arrays spec section 18
rules that the first release needs no new loop syntax, sketches FOR EACH as
MAY-add with syntax not yet normative, and requires structural-mutation
detection during iteration -- for which the runtime's `mutation_sequence` /
`structure_sequence` fields already exist on every ArrayValue. The outside
recommendation and the inside spec agree, and the spec got there first with
the guard rails.

Disposition: control flow stays out of AIF-109's build scope (the evaluation
itself ranks it "in good shape"); the three collisions are recorded here so
no future CASE/EXIT/continue work starts without them; the counted-FOR and
general-loop gaps ride the same call-frame lane review, since frames change
what any new loop may enclose.

## 2. DEFFN and DEFCMD: seams built, evaluation absent

Both exist, both are `status: experimental`, both are session-only and never
written to disk. Their own usage contracts state their limits honestly --
which is why this is **not** an AIF-079 declared-but-unimplemented instance;
the house annotation convention prevented a false positive.

- `DEFFN <NAME> = <body-text>` registers a custom function through the
  `fn_custom` seam. It **resolves inside `?` / `CALC` / `WHERE`**, and
  **refuses to shadow a compiled-in builtin**. Its contract says plainly:
  *"MVP body returns the stored text (arguments are accepted but ignored)."*
- `DEFCMD <NAME> = <body-text>` registers a session-scoped Extension command
  with a real handler signature `(DbArea&, istringstream&)`. Invoking it
  prints the stored body plus trailing arguments -- explicitly *"useful for
  routing/parse checks."*

**Consequence for any function lane:** runtime registration, expression-path
resolution, namespace protection against builtins, and command-path
registration are already built and exercised. What is missing is parameter
binding, body *execution* rather than text return, and `RETURN`. That is a
materially smaller and better-anchored job than "no UDF facility exists."

## 3. What the arrays spec already decides for functions

`DOTSCRIPT_ARRAYS_SPEC_V1.md` is normative for planned implementation and
governs more than arrays. A function surface does not get to re-open these:

- **Section 19, Procedure and Function Parameters.** "Arrays pass as
  reference values; element mutation affects the caller's shared array.
  Rebinding a local parameter (`$VALUES = {}`) changes only the local binding
  unless explicit by-reference binding is later added (out of scope; **design
  consistently for all DotScript types**)." Parameter semantics are settled,
  and the consistency clause binds every future type.
- **Section 11, Reference Semantics.** The Clipper/Harbour value model:
  assignment shares the reference; `ACLONE()` is an independent recursive
  copy that *preserves shared child topology*; `ASAME()` is identity, `==` is
  structure. This is the copy-versus-share rule locals inherit.
- **Section 5, Value Model.** An array is an ordinary expression `Value`, and
  the enumerated future element kinds explicitly include **`callable`**. A
  function value is anticipated by the value model rather than bolted beside
  it.
- **Section 7, Grammar.** `{|` is **reserved for future code blocks**. The
  grammar has already parked a callable literal syntax; a function lane must
  not spend that token on something else.
- **Section 27, Runtime Limits.** Configurable caps (1,000,000 elements,
  depth 64, 256 MB total), applied **before** substantial allocation, with
  `SET ARRAY MAXELEMENTS|MAXDEPTH|MAXBYTES` routed through ordinary SET. Call
  frames need the same treatment -- recursion depth is the same class of
  hazard as nesting depth.
- **Section 29, Error Contract.** A catalogued, localizable, SelfDoc-usable
  message-id family with templated text. Any `TRY`/`ON ERROR` work should
  extend this contract, not invent a parallel one.
- **Section 13, Cycle Policy.** Direct and indirect cycles prohibited before
  mutation, with the reason stated: a refcounted runtime cannot safely
  reclaim them. Implemented as `would_create_cycle`.

## 4. The tuple boundary, and TUPTALK

**Section 20** draws the line the owner's pointer was aimed at: an array is
positional, mutable, one-based, script-owned and heterogeneous -- for lists,
arguments, intermediates and algorithms. A **tuple** is field-aware and
named, tied to work areas, records, relations and streams, with its own
live-versus-snapshot lifecycle. Arrays may *contain* tuples but must not
replace tuple streams or semantics.

**TUPTALK, measured:** a process-wide `std::vector<TupEntry>` where each entry
carries field type, length, decimals, the raw slice and its normalized form;
`PUSH` captures fields or whole rows from the live DBF record, and `PUSH ROW`
builds a fixed-width, schema-aligned row through
`cli::fixed_width::build_schema_aligned_row`. It is an **in-memory typed row
builder with no table beneath it** -- the tuple side of section 20, already
running as a normalization harness.

**Section 21** specifies the bridges: `TUPTOARRAY(tuple)`,
`ARRAYTOTUP(array, schema)` (only after validating field count, names, types
and constraints), and `TUPMATERIALIZE(stream, limit [, mode])` -- where the
limit "SHOULD be mandatory unless the stream is known finite," to prevent
loading millions of records into script memory. Designed; not built on this
reading.

## 5. MINIDB reconciliation against sections 23 and 24 (owed, now done)

Yesterday's memo-resident mini-database container was designed without
reading this spec. The check:

**Consistent.** Section 23 states the separation MINIDB depends on: `DbArea`
stores a MemoRef, `MemoManager` owns the payload, and a carrier "does not
interpret, stream, clone, repair or persist payloads." MINIDB is a
*convention over an agnostic store*, not a store feature -- which is exactly
this separation honored. Section 24 confirms the shape: "Encoded arrays may
be stored via the memo subsystem ... the DBF stores the memo reference, not
the array." MINIDB stores a container and the row stores its token. No
conflict.

**Two divergences worth recording rather than fixing today:**

1. **Content type has two homes.** Section 24 imagines a media type at the
   write call (`MEMOPUT(JSONENCODE($A,"TYPED"), "application/json")`), while
   MINIDB records its format in the catalog row's `FMT` column and repeats it
   as the payload's first line. Both are defensible; they should not both
   become normative without a ruling.
2. **Serialization modes.** Section 24 names `PORTABLE` versus `TYPED` modes
   for round-tripping values whose type would otherwise be lost. MINIDB has
   no mode concept -- it does not need one for raw file images, but a future
   container carrying *values* rather than files would, and should adopt this
   vocabulary rather than coin another.

**One pattern MINIDB should copy outright:** section 17's `ARRAY` diagnostic
family -- `INFO`, `LIST`, `VALIDATE`, `STATS`, `LIMITS`, `TRACE` -- is a
ready-made shape for the chartered `WORKSPACE VERIFY` and the workspace
budget reporting. Same problem, already designed once.

## 5b. STOP_ON_ERROR, measured properly (owner pointer: "search for stop on error")

The first pass understated this surface. What exists beneath the threshold
command is most of an error-handling *runtime*, missing only the script-level
reaction:

- **A canonical error state** (`xbase::error`, `xbase_error_context.hpp`):
  a typed, thread-local last-error `code` (HRESULT-style per `ERROR_STATUS`),
  with `set_last_error` / `get_last_error` / `clear_last_error` -- and an
  **error generation counter** that increments on every recording. That
  counter is a ready-made change-detection primitive: "did anything error
  between two points" is already answerable in one comparison.
- **Severity classification at the source.** `STOP_ON_ERROR`'s contract:
  the threshold "is compared against the severity carried by the canonical
  error code recorded through the message/emit_error path (errors derive
  from messaging), so only real recorded errors can trip it." Errors are
  catalogued messages with severities -- the same contract family the arrays
  spec's section 29 extends.
- **A full inspection command family**: `ERROR_STATUS` (structured display),
  `ERROR_CLEAR`, `ERROR_TEST` (subsystem self-test), plus the `SET ERRORSTOP`
  compatibility form and a `DOTTALK_ERRORSTOP` environment default.
- **Its own lane history** (`DOTSCRIPT_STOP_ON_ERROR_LANE_V1.md`, AIF-036):
  the runtime predated the command, and the runtime's comment *named its
  future consumer* before that consumer existed -- the declared-future done
  correctly, the opposite of the AIF-079 shape.

**The one measured hole:** no expression-visible error probe. Nothing in the
function catalog exposes last-error or the generation counter to a script
expression -- `ERROR_STATUS` prints for humans, but a script cannot ask.
Which means the cheapest first increment toward "error handling" is not
control-flow syntax at all: **one or two catalog functions** (an error-state
probe and/or a generation read) would enable a scripted poor-man's TRY today
-- `ERROR_CLEAR`, attempt, compare generation, branch -- using only existing
runtime state and the existing `IF`. Structured `TRY`/`ON ERROR` remains the
destination; this is the measured on-ramp, and it re-ranks ruling 5 in the
list below: the choice is no longer binary between "new construct" and
"threshold extension" -- there is a third, smaller option that ships value
before either.

## 5c. The block family: buffer-and-replay already exists (owner pointer:
## "scan/endscan loop/endloop, et al")

Measured: DotScript already has a full begin/end block family, and every
member works the same way -- **the begin command switches the shell into
buffering, lines are captured instead of executed, and the end command
replays the stored body**:

| Construct | Contract language (from the source) |
| --- | --- |
| `SCAN [FOR] ... ENDSCAN` | "Buffer and execute a SCAN...ENDSCAN record loop over the current logical rowset" |
| `LOOP [<n>] ... ENDLOOP` | "Start buffering commands for later replay by ENDLOOP" -- with a count form |
| `WHILE <expr> ... ENDWHILE` | "begin buffering; shell must route lines to WHILE_BUFFER" |
| `UNTIL <expr> ... ENDUNTIL` | same shape, inverted condition |
| `IF / ELSE / ENDIF` | conditional block on the shell's shared boolean evaluator |

**Consequence, and it is the largest reduction in this note:** body capture,
body storage, and body replay -- the entire mechanical substance of a
`FUNCTION ... ENDFUNC` definition -- are already implemented five times over.
A function definition is the same buffering gesture with one difference at
the end marker: instead of *executing* the captured body, `ENDFUNC` files it
in the registry `DEFFN` already owns. A call is a replay with a frame around
it. The function lane is therefore not "build a body parser"; it is "route
existing buffer machinery into an existing registry, and add the frame."

**The shared ceiling, confirmed:** `SCAN` carries an explicit re-entrancy
guard -- "nested SCAN not allowed during ENDSCAN" -- the same one-level shape
as DOTSCRIPT's one-subscript limit. The whole block family sits under the
same no-frames ceiling, which means call frames lift *all* of these
restrictions as one piece of work, not as per-construct fixes.

**Closer measurement of the three replay loops (owner pointer round two)**
sharpens this further:

- **The replay engine is already a named, injectable seam.** LOOP's contract:
  "ENDLOOP executes buffered commands through the *pluggable shell
  executor*"; WHILE and UNTIL both execute "through the *canonical loop
  executor*." A function call is the same executor invoked with a frame --
  the execution seam does not need to be built, only parameterized.
- **The house has already picked a replay cap:** LOOP carries a "hard default
  max iterations: 1000," clamped rather than errored. The recursion-depth
  ruling (section 6, item 4) has a sibling precedent and a house number
  style to match.
- **Buffers persist after execution** -- both WHILE and UNTIL state "buffer
  persists after ENDWHILE (mirrors ENDLOOP behavior)." A stored body already
  outlives its run; it is one naming step away from being a definition.
- **A label form is parked in the grammar:** `LOOP FOR <label>` "stores a
  nonnumeric label and currently replays once" -- an honestly-declared MVP
  stub that is, structurally, a named body waiting for semantics.
- **Deliberate buffer isolation, recorded as intent:** WHILE and UNTIL are
  "private buffering (no loop_state deps)" twins (263 lines each) with
  separate WHILE_BUFFER / UNTIL_BUFFER routing. Three buffers is a design
  choice here, not drift -- but any frame work should unify at the executor
  seam rather than adding a fourth private buffer.
- **WHILE/UNTIL are record loops**, not general loops: execution "starts at
  the current record and advances one record per iteration." A general
  conditional loop and a function body replay both belong to the
  executor+buffer layer beneath that record-advancing policy.

**And the record-loop engine ties back to error handling:** the unified
harness (`dt::predicate::loop_records`, serving SCAN / COUNT / DELETE FOR /
LIST FOR) already models what section 5b needs a probe for -- its `LoopSpec`
carries `stop_on_error` and its `LoopResult` returns `visited / matched /
acted / aborted / last_error`. Abort-with-reason is an existing result shape
in the tree, one seam below the script surface.

## 6. Owner rulings (RESOLVED 2026-08-12)

All five ruled in one sitting. Governing doctrine the owner set for the whole
set, coined here and promoted to the glossary:

> **"We are not a clone; that ship has sailed, so we get to improve the
> product when we step out of the box. Go for gold unless the cost is
> platinum."** -- when the better design and the clone-faithful design
> diverge, take the better one, because fidelity to a discontinued lineage is
> not itself a goal. The only brake is disproportionate cost (platinum): a
> gold design is chosen unless it would cost far out of proportion to what it
> buys. This is the affirmative twin of "it costs nothing to do it right" --
> that rule forbids cheapening a free correct act; this one forbids
> defaulting to the merely-faithful when the better answer is affordable.

1. **Parameter surface: SIGNATURE ON THE FUNCTION LINE.** `FUNCTION
   ADDTAX($AMT, $RATE)`, not a `PARAMETERS` body line. RULED. The signature
   is visible where the function is named -- a reader and a future
   `FUNCTION LIST` both learn arity without opening the body -- and it is the
   form that AGREES WITH THE SCOPE MODEL in ruling 2 (Pascal declares its
   parameters in the header). Go-for-gold over the older `PARAMETERS`-line
   fidelity; the parenthesized parameter list is the parser's one new piece.
2. **`LOCAL` explicit-declared, Pascal-style procedure scope.** RULED.
   Declared, not inferred (an override may come later). Scope is
   procedure-level and NESTS: a variable declared in a procedure is visible to
   that procedure AND the procedures it calls, unless an inner declaration of
   the same name shadows it. This is close to classic xBase PRIVATE (visible
   down the call chain, shadowable), so the gold choice is also the faithful
   one here -- no tension. Pure lexical isolation is the thing NOT chosen.
3. **Function bodies live inline in the `.dts`.** RULED. Not a separate file,
   not runtime `DEFFN` registration. Rides the existing buffer-and-replay
   machinery (section 5c) with no new file-loading path; most teaching-legible
   because the definition sits where it is used.
4. **Recursion depth cap: hard 1000, as a named constant.** RULED. Matches
   LOOP's existing hard-max precedent; a constant (greppable, one-edit
   change), never a literal. Strict-first per the growth doctrine; a dynamic
   cap can come later behind the same constant.
5. **Error model: expose the state, keep the threshold; defer TRY/CATCH.**
   RULED, and reframed by the owner: error handling is not a missing
   construct -- the POLICY already exists as `STOP_ON_ERROR OFF | WARNING |
   ERROR`, which is precisely "bypass so scripts complete even if one item
   fails" versus "hard stop when continuing would be dangerous for the rest
   of the script." The work is to make that policy SCRIPTABLE and
   INSPECTABLE: one or two catalog functions exposing last-error and the
   generation counter to expressions, so a script can make the
   bypass-or-stop decision PER OPERATION with the existing `IF`, not only
   globally. Uses the severity classification and generation counter that
   already exist (section 5b). `TRY`/`CATCH` as a block construct is a
   later maybe, not this lane -- the smaller, more xBase-faithful surface
   ships first and may prove sufficient (demonstrated-negation candidate:
   show the scripted probe covers the real cases before building blocks).

## 7. Recommended sequencing (proposal only)

1. **Call frames first** -- parameters, `LOCAL`, `RETURN`, and the nesting
   limit removed as a consequence. Two of the three critical gaps are one
   piece of work, and section 19 already fixes their semantics.
2. **Promote `DEFFN`/`DEFCMD`** from text macros to real definitions on the
   seams they already own, rather than adding a parallel facility.
3. **Error handling as its own lane**, extending the section 29 contract.
4. **Tuple bridges** when the function surface needs to return structured
   data -- section 21 is specified and TUPTALK is the working half.

Section 6 is now RULED, so this sequencing is cleared to become a charter.
The lane it feeds: `FUNCTION NAME($params)` with signature-line parameters,
`LOCAL` declarations with Pascal nesting scope, `RETURN`, inline bodies,
recursion capped at a named 1000, and the nesting limit removed as the
consequence of call frames -- then the error-state catalog probe as the
second increment. No further owner ruling gates the build; the writeback-side
rulings (verb name, MINIDB compaction, content-type home) are a SEPARATE
sitting and do not block this lane.

---

*Prior art wins again: the sharpest constraint on a feature nobody has
started was written six days earlier, in a document about something else.*
