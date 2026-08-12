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

## 6. What is genuinely undecided

These are owner rulings, not research questions:

1. **Declaration surface for parameters** -- an xBase-faithful `PARAMETERS`
   line inside the body, versus a signature on the `FUNCTION` line. Both are
   period-correct; only one should be taught.
2. **`LOCAL`: declaration or inference.** Explicit declaration is
   xBase-faithful and teaching-legible; inference is friendlier and quietly
   changes what a bare assignment means inside a frame.
3. **Where a function body lives** -- inline in a `.dts` file, in its own
   file, or registered at runtime through the existing `DEFFN` seam. The
   third is the cheapest and the least conventional.
4. **Recursion depth cap** -- section 27's numbers cover data; call frames
   need their own, and the strict-then-dynamic doctrine says pick a number
   and refuse clearly.
5. **Error model shape** -- whether `TRY`/`CATCH` is a script-level construct
   or an extension of the existing `STOP_ON_ERROR` threshold with a handler
   hook. The second is smaller and less teachable; the first is what the
   evaluation asked for.

## 7. Recommended sequencing (proposal only)

1. **Call frames first** -- parameters, `LOCAL`, `RETURN`, and the nesting
   limit removed as a consequence. Two of the three critical gaps are one
   piece of work, and section 19 already fixes their semantics.
2. **Promote `DEFFN`/`DEFCMD`** from text macros to real definitions on the
   seams they already own, rather than adding a parallel facility.
3. **Error handling as its own lane**, extending the section 29 contract.
4. **Tuple bridges** when the function surface needs to return structured
   data -- section 21 is specified and TUPTALK is the working half.

Nothing above should be built before the owner rules on section 6.

---

*Prior art wins again: the sharpest constraint on a feature nobody has
started was written six days earlier, in a document about something else.*
