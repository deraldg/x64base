---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-010
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  git:
    branch: development
    baseline_commit: 57c2d1634
  project:
    id: project.x64base.runtime
  authorization:
    requested_by: maintainer (member.derald), in-session, "go"
    scope: >
      Lane charter. Root cause traced to file:line from runtime observations
      made during the AIF-112 Phase-1 exercise. No source mutation proposed
      here; the remedy options are options. AIF-117 claimed host-side by the
      owner via session_coordinator.py claim-aif; not self-assigned.
  lane: AIF-117
  lane_found_in: AIF-112
  lane_siblings: AIF-116, AIF-114
  report:
    path: docs/maintenance/SILENT_PREDICATE_AND_STORE_FAILURES_LANE_V1.md
    kind: lane_charter
  primary_topics:
    - "FieldRef::eval"
    - "predicate evaluation"
    - "silent failure"
    - "error surfacing"
    - "scan_selector"
---

# Silent Predicate and Store Failures -- the Engine Diagnoses, the Command Discards (Lane V1)

**Status:** root-caused, not started. **Lane:** AIF-117
(claimed 2026-08-15, run `COWORK-20260815-001`, lane
`silent-predicate-and-store-failures`).
**Evidence class:** `runtime_observed` plus file:line source confirmation.
Runtime observations at banner `fe42666e dirty`, source read at `57c2d1634`.
**Found:** during the AIF-112 Phase-1 exercise, 2026-08-15, by running the
ledger rather than by reading the code.

## 1. The one-sentence version

A bare field used as a predicate is evaluated as **"is this field non-blank"**,
so `COUNT FOR SUP` matches every row whether `SUP` is `T` or `F`; and an
unresolvable field yields the empty string, so `COUNT FOR NOSUCHFIELD` matches
nothing and says so as though it were an answer.

Both return a confident, plausible, wrong number. Neither reports anything.

## 2. Measured

Live, against a five-row `INVCHKOUT` where `SUP` is `T` on three rows and `F` on
two:

```
. count                     -> 4      (at the time, 4 rows)
. count for sup             -> 4      WRONG, should be 2
. count for nosuchfield     -> 0      WRONG, should be an error
. count for sup = T         -> 3      correct (after a 5th row)
. count for state = "held"  -> 2      correct
. ? SUP                     -> T      (record 1)
. ? SUP                     -> F      (record 2)
. displaay                  -> Unknown command: DISPLAAY
```

The last two lines are the shape of the problem. **`?` reads the field
correctly per record**, so nothing is wrong with storage or with the expression
layer's ability to see the value. And an unknown *command* is refused by name
while an unusable *predicate* is not.

## 3. Root cause, file:line

`src/cli/expr/eval.cpp:21`

```cpp
bool FieldRef::eval(const RecordView& rv) const {
  if (!rv.get_field_str) return false;
  auto s = rv.get_field_str(name);
  for (char ch: s) {
    if (!std::isspace(static_cast<unsigned char>(ch))) return true;
  }
  return false;
}
```

That is non-blankness, and it is the only truth test a bare `FieldRef` has.

- `SUP` -> raw byte `'T'` or `'F'` -> both non-whitespace -> **true every row**.
- `NOSUCHFIELD` -> `get_field_str` yields `""` -> loop never runs -> **false
  every row**, and the function never asks whether the field exists.

**Why it reaches that function.** `include/cli/expr/ast.hpp:19` defines
`RecordView` with exactly two accessors:

```cpp
struct RecordView {
    std::function<std::string(std::string_view)> get_field_str;
    std::function<std::optional<double>(std::string_view)> get_field_num;
};
```

No type, no existence. `FieldRef::eval` uses the only tool it has.

**Why nothing complains.** `value_eval.cpp` wraps any non-literal node as a
boolean without inspecting it:

```cpp
try {
    ev.kind = EvalValue::K_Bool;
    ev.tf = prog->eval(rv);
    return ev;
} catch (...) { ... }
```

So a `FieldRef` result is a valid `K_Bool` and never reaches the
`"FOR/WHILE must evaluate to logical/boolean"` guard below it. And in
`src/cli/scan_selector.cpp`, `collect_selected_recnos`:

```cpp
bool result = false;
std::string err;
ok = dottalk::expr::eval_bool_compiled(*compiled, area, result, &err) && result;
if (!ok) continue;
```

**`err` is declared, passed by address, and never read.** An evaluation failure
silently `continue`s, excluding the row. Every selector-backed command inherits
this -- `COUNT`, `LIST FOR`, `SUM`, and the rest -- not just `COUNT`.

### Candidates eliminated on the way, recorded so nobody re-walks them

- **The predicate-chain fast path is not involved.** `predicate_chain.cpp`'s
  `parse_cond` requires `FIELD OP VALUE`; a lone identifier fails at the
  operator, `try_eval_predicate_chain` returns "not a chain", and evaluation
  falls through to `compile_where`.
- **`logical_to_num` is correct** (`glue_xbase.cpp:61`): `T`/`.T.`/`Y`/`1`/`TRUE`
  -> 1.0, `F`/`.F.`/`N`/`0`/`FALSE` -> 0.0. The comparison path is fine, which is
  why `SUP = T` works.
- **Logical storage is correct.** `T`/`F` on disk; `normalize_logical_value`
  accepts the dotted forms and strips them. Nothing to fix in the representation.
- **`eval_bool`'s strict tail is correct** and is simply never reached for this
  input.

## 4. The family -- one defect, four faces

| Finding | Lower layer knows | What the operator sees |
|---|---|---|
| **G1a** bare logical predicate | -- (`FieldRef::eval` has no type) | every row matches |
| **G1b** unknown field in predicate | `filter_registry.cpp:201` has `"unknown field ..."` on the SET FILTER path; this path has nothing | no rows match, reads as a real answer |
| **F1** `REPLACE` with a bad RHS | `validate_field_value_for_store` has `"invalid date for field"` | field silently blank, success reported |
| **E2** `UNLOCK` on an unlocked record | -- | `"record N unlocked"`, indistinguishable from a real release |
| **A3** `APPEND BLANK` | parser rejects `BLANK` | error, then subsequent REPLACEs clobber the current record |

The through-line: **the engine's lower layers usually detect the problem, and
the command layer discards the diagnosis and answers anyway.** `DISPLAAY` proves
the codebase can be strict; it is currently strict about the typo that cannot
hurt you and permissive about the ones that can.

**Why this is not cosmetic.** These were found while building a document-control
ledger. "How many items are still checked out" answered `0` because a column name
was misspelled is not a wrong number, it is a **wrong number that reads as good
news**. An inventory system exists to prevent exactly that.

## 5. Remedy options -- none chosen

**R1. Make `FieldRef::eval` type-aware.** The natural fix. A logical field's
truth value is its value; a numeric field's is `!= 0`; only character and memo
fall back to non-blankness.

The blunt version -- try `get_field_num` first, use `!= 0.0`, else fall back to
non-blank -- is one line and **changes character-field semantics**:
`get_field_num` applies a soft numeric normalization to `C` fields
(`glue_xbase.cpp:223`), so a character field containing `"0"` would flip from
true to false. Small, real, and must be decided rather than discovered.

The clean version adds a third accessor to `RecordView`
(`get_field_type`), populated in both `make_record_view` and
`make_record_view_raw`, and dispatches on it. Slightly larger, unambiguous, and
gives every future node the type information the AST currently lacks.

**R2. Surface the error in `scan_selector.cpp`.** Read the `err` that is already
being filled and report it instead of `continue`. One line to read it, a few to
route it. Independent of R1 and worth doing regardless.

**R3. Make an unresolvable field name an error, not a false.** Requires an error
channel out of `Expr::eval`, which currently returns a bare `bool`. The callers
already `catch (...)`, so an exception would propagate -- but `scan_selector`
turns a caught exception into `ok = false`, silently excluding the row, so **R3
does not work without R2**. Sequence matters.

**R4. Audit the family.** F1, E2 and A3 are separate call sites with the same
shape. Fixing G1 alone leaves the pattern.

**R5. A gate.** The durable form: no command may discard an error out-parameter
it passed. Approximable by grepping for declared-and-unread error strings at
call sites. Per `PREPUSH_GATE_REFERENCE_V1.md`, "obligations carrying a gate held
83-94 percent compliance; the one without a gate held 33."

## 6. Not proposed

- No change to logical storage. `T`/`F` on disk is correct and the dotted-form
  stripping is correct.
- No change to `logical_to_num`, `normalize_logical_value`, or the comparison
  path. All three are right.
- No change to the predicate-chain fast path. Not implicated.

## 7. Acceptance

1. `COUNT FOR <logical-field>` equals `COUNT FOR <logical-field> = T`.
2. `COUNT FOR <unknown-field>` reports an error and does not return a count.
3. A `REPLACE` whose RHS fails to evaluate reports the failure and does not
   store blank (F1).
4. Character-field predicate semantics are stated explicitly in a test, whatever
   is decided for the `"0"` case, so the decision is recorded rather than
   implied.
5. `LIST FOR`, `SUM`, and the other selector-backed commands are covered, not
   just `COUNT` -- the defect lives in the shared selector.

## 8. Ties

- **AIF-112** found it. The ledger is the reason it matters.
- **AIF-116** is the same session's other defect and the same shape one layer
  down: a value that could not be trusted, and no gate.
- **AIF-114** (published `SET` options with no implementation) is the
  documentation face of "stated but not enforced".
- `proof.governance.availability_is_not_adoption` -- the registry entry on
  proof failures. This lane is a candidate second entry: **the defect was found
  by an oracle the scribe had openly described as weak**, which is an argument
  about the value of a second opinion even when it is a poor one.

---

Owner `member.derald`. Finder and steward `member.ai.claude.cowork`.
Runtime observations operated host-side by the owner; every source claim
verified against the tree.
