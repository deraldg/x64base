---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260729-003
  recorded_at_utc: 2026-07-29T23:55:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: member.derald
    owner: member.derald
    committer: member.derald
  session:
    id: not_exposed
    chat_reference: MAINTAINER_ATTESTED
    run_id: AIPR-20260729-001
    chat_handle: ""
    handle_binding: MAINTAINER_ATTESTED
    continues_run: null
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 22124a5d0
  authorization:
    requested_by: maintainer
    scope: AIF-074 P4.0 -- evaluator differential harness, scope and cost
  report:
    path: docs/maintenance/EVALUATOR_DIFFERENTIAL_HARNESS_SCOPE_V1.md
    kind: scope
---

# Evaluator Differential Harness -- Scope and Cost

**Date:** 2026-07-29 - **Status:** `implemented-findings` - **Lane:** AIF-074 (P4.0a)
**Owner:** `member.derald` - **Author:** `member.ai.claude.cowork`

## Why this exists

`BUFFER_VISIBILITY_TWO_FAMILIES_V1.md` established that x64base reads rows two
ways. That finding is architectural: it says the families exist and that defects
live where they mix. It does NOT say whether the two families, given the same
record and the same predicate, actually **agree**.

Nobody has ever checked. That is the gap this harness closes, and it must be
closed before P4 unifies anything, because:

- If they agree everywhere, migrating SQLsel's `WHERE` to the tuple path is a
  mechanical change and platinum gets cheaper to price.
- If they disagree, that is a finding on the scale of the two-families work, and
  it arrives BEFORE a seam locks a decision in.

Either answer is worth more than the harness costs. That asymmetry is the case
for building it first.

## What it compares

One record. One predicate expression. Two evaluators. Same verdict?

| Path | Entry point | Binds to |
|---|---|---|
| Classic | `expr::compile_bool_predicate(area, e)` + `eval_bool_compiled(pred, area)` | `DbArea` current record |
| Tuple | `expr_tuple_glue` bound to a `TupleRow` | `TupleRow` built from that record |

**Critical design point.** The comparison must call the two EVALUATORS directly,
in-process, on the same positioned record. It must NOT compare two COMMANDS
(e.g. `SQLSEL ... WHERE` against `SMARTBROWSER ... FOR`). Command-level
comparison conflates evaluator semantics with buffer overlay, cursor handling and
rendering -- which is exactly the confusion that made the two-families question
hard to answer in the first place. The tuple side runs with
`overlay_table_buffer=false` so that buffering is held constant and the ONLY
variable is the evaluator.

## Predicate corpus (the part that does the work)

A harness that runs three easy predicates proves nothing. The corpus targets
places where two independent implementations plausibly drift:

- **Character equality and padding** -- `LNAME = "SMITH"` against a space-padded
  C field; trailing-space semantics are a classic xBase divergence.
- **Typed equality** -- `SID = 50000000` vs `SID = "50000000"`. Numeric-vs-string
  comparison was a live defect in the REL path THIS WEEK (RDB-03, fixed 2026-07-29);
  it is the single most likely place for the two evaluators to differ.
- **Blank handling** -- `MAJOR = ""`, `EMPTY(MAJOR)`. R16 ruled blank is a value;
  this asserts both evaluators honor that ruling identically.
- **Numeric boundaries** -- decimals, negative, zero, and the declared width edge.
- **Date** -- comparisons and `DTOS`/`CTOD` round-trips.
- **Logical** -- `.T.`/`.F.` literals against an L field (P1.6 slice 1 taught the
  lexer these; this checks both evaluators read them the same way).
- **Functions** -- `ALLTRIM`, `UPPER`, `SUBSTR` inside a predicate.
- **Compound** -- `AND` / `OR` / `NOT` nesting and precedence.
- **Failure parity** -- an unknown field, a type-mismatched comparison, a
  malformed expression. Both paths must FAIL, and ideally fail the same way.
  Divergent error behavior is a defect even when neither answer is wrong.

## Fixture

The 200-row x64 `STUDENTS` fixture covers C, N and D with real data, but has no
L field and no deliberate blanks. The harness needs a small purpose-built
SANDBOX table carrying every field type plus deliberate edge rows (blank in each
type, boundary numerics, a deleted record). Self-bootstrapping and self-erasing,
per the regression doctrine already in force.

## Cost

| Item | Estimate | Note |
|---|---|---|
| Dev command `EVALDIFF` | ~200-250 lines | Positions each record, evaluates the corpus both ways, reports divergences |
| Surface registration | small but REAL | registry entry, `@dottalk.usage` contract, a `dotref` entry -- omit the last and normcheck reports a phantom |
| Fixture + corpus | ~100 lines of `.dts` | Self-bootstrapping SANDBOX table |
| Regression + registration | small | `EVALDIFF` row in the curated catalog |
| **Total** | **one focused slice** | No engine semantics change; the harness only observes |

**Risk: low.** It adds a dev-only observer. It changes no existing behavior, and
it cannot break a shipped surface -- which is precisely why it is safe to do
before the migration that can.

## Good / better / best

- **Good** -- throwaway probe. Answers the question once, adds no command
  surface. Cheapest. Cost: the answer is not durable, and divergence could
  silently reappear later with nothing watching.
- **BETTER (GOLD, recommended)** -- permanent dev command plus a registered
  regression. The question is answered AND stays answered; any future change that
  makes the evaluators disagree gets caught by a named, runnable gate. Marginal
  cost over the throwaway is the surface registration.
- **Best** -- gold, plus promotion into the default `REGRESSION ALL` suite once
  soaked. Barely more than gold (it mutates only SANDBOX and is not long-running),
  so this is NOT a platinum rung -- it is the natural end state of gold after one
  green cycle.

Per R23, gold is the default and is what proceeds unless the owner objects.

## What this does NOT do

It does not migrate anything, introduce the seam, or change SQLsel. It answers
one question -- do the two evaluators agree? -- so that P4.0's design is chosen
on measurement instead of assumption. If the answer is "they agree everywhere",
that is a cheap and genuinely good result, and it should be recorded as such
rather than treated as a wasted slice.

## 2026-07-30 implementation result

The GOLD harness is implemented as:

- `src/cli/cmd_evaldiff.cpp` -- permanent observer command and usage contract;
- `EVALDIFF` entries in the shell registry and `include/dotref.hpp`;
- `dottalkpp/data/scripts/evaldiff_regression.dts` -- four-row typed X64
  SANDBOX fixture, predicate corpus, cursor check, and self-erasure;
- `REGRESSION EVALDIFF` -- curated, explicit-run registration.

Build and real-runtime execution both completed. The durable transcript is
`labtalk/proofs/runs/20260730_evaldiff_p4_0a.txt`. The fixture erased cleanly
and the before/after cursor assertions were both true.

The measured answer is **NO: the evaluator families do not agree across the
required corpus.** The refined 20-predicate run reports 10 `VERDICT-PARITY`,
2 `PARITY-ON-FAILURE`, and 8 `DIFFERENCES` summaries. Those eight differing
predicates are not eight independent defects.

### Two root-cause clusters behind the differences

| Finding | Runtime fingerprint | Source confirmation |
|---|---|---|
| ED-01: the TupleRow AST route does not parse function calls | A function on the left collapses to TRUE on all four rows; `CTOD` on the right collapses to FALSE. The impossible control `ALLTRIM(CVAL) = "ZZZZZ"` still returns tuple 4/0/0 while classic returns 0/4/0. `UPPER("ALPHA") = "ALPHA"` shows the behavior does not require TupleRow field access | `Parser::nud` maps every identifier directly to `FieldRef`; there is no function-call production. `Parser::parse_expr` returns without requiring end-of-input, so the remaining `(...) = ...` tokens can be ignored |
| ED-02: classic `EMPTY()` loses its logical type | classic returns ERROR on all four rows for both `EMPTY(CVAL)` and `EMPTY(NVAL)`; tuple returns TRUE on all four | `dt_empty` returns `.T.` / `.F.` text. Classic preprocessing quotes that non-numeric result as a string literal; `eval_bool` then rejects the resulting string because it is neither boolean nor numeric |

This is one TupleRow function-call/parser defect plus one classic `EMPTY`
logical-typing defect. `ALLTRIM`, `UPPER`, `SUBSTR`, `DTOS`, and `CTOD` are
examples exposing ED-01, not five separate function implementation defects.

### Parity is not correctness

Three `VERDICT-PARITY` cases are settled wrong answers, not clean results:

| Predicate | Both paths report | Why it is wrong |
|---|---|---|
| `DELETED()` | TRUE on all four rows | the fixture has exactly one deleted row, record 4 |
| `NOSUCH = "X"` | FALSE on all four rows | an unknown field silently becomes an empty result instead of a reported name error |
| `NVAL = "NOTNUM"` | FALSE on all four rows | an incompatible numeric-vs-string comparison silently becomes no match |

The compound predicate containing `EMPTY()` and the malformed-parenthesis
control now report `PARITY-ON-FAILURE`, not `PASS`: both evaluators failed every
row, so no verdict was evaluated. No EVALDIFF summary uses `PASS` now.

This is a hard scope boundary for the tool: `VERDICT-PARITY` proves only that
the two outcome classes match. It never proves that either outcome is correct.
Correctness requires an expected-result or external-oracle assertion.

**Gate disposition:** harness delivery is complete; evaluator parity is RED.
P4.0b is not mechanical and must not migrate SQLsel's `WHERE` onto the tuple
path until ED-01 and ED-02 are repaired and the shared silent-wrong-answer cases
are converted to reported failures under explicit oracle cases. The harness
itself changes neither evaluator.
