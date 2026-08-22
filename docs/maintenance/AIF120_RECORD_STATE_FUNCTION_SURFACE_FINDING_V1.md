---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-104
  recorded_at_utc: 2026-08-22T02:05:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: b521465f4
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 --
      "look for commands and functions in help, look for index and order
      information in include and src". Report only; no fix authorised.
  report:
    path: docs/maintenance/AIF120_RECORD_STATE_FUNCTION_SURFACE_FINDING_V1.md
    kind: finding
---

# AIF-120 -- R114: the expression layer has almost no record-state functions, and the two it has are uncatalogued

Status: **finding, review-needed. REPORTED, NOT FIXED. NO BUILD AUTHORISED.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `b521465f4`.

**Area:** engine (`src/cli/expr/`). **Not this lane's code**; a report, not a
change.

This explains a limitation two shipped regression specs already worked around by
trial and error, and records the reason so the next person does not rediscover it
empirically.

---

## 1. Measured

**The catalog.** Registered expression functions, counted from the registration
tables themselves (`fn_numeric.cpp`, `fn_string.cpp`, `fn_date.cpp`,
`fn_custom.cpp`, `function_catalog.cpp`, idiom `{ "ABS", 1, 1, &num_abs },`):

    registered expression functions: 73

That agrees exactly with the `HELP FUNCTIONS` render in the 2026-08-22
`REGRESSION ALL` transcript -- NUMERIC 21, DATE 22, STRING 17, SEARCH 4,
LOGICAL 3, CONSTRUCTION 3, CONVERSION 3 = 73. Two independent counts, same
number, so the catalog **is** the published surface.

**What is not in it.** Twelve record-, cursor- and index-state names, checked
against that list:

| name | in catalog |
|---|---|
| `RECNO` `FOUND` `BOF` `EOF` | **absent** |
| `DELETED` `RECCOUNT` | **absent** |
| `INDEXSEEK` `ORDER` `TAG` | **absent** |
| `DBF` `ALIAS` `SELECT` | **absent** |

**Not zero, though -- exactly two live outside the catalog.**
`src/cli/expr/glue_xbase.cpp` surfaces two special symbols directly to the
predicate evaluator, bypassing registration:

- `:162` -- `DELETED` -> `area.isDeleted() ? "T" : "F"`
- `:172` -- `RECCOUNT` -> `area.recCount64()`

The `RECCOUNT` site carries an owner correction dated 2026-08-12 explaining why
it exists (a record count is a fact in the header, not something a loop derives).
So it was added deliberately -- and added **beside** the catalog rather than
into it.

## 2. What this explains

Two shipped specs record the symptom without the cause.

**IDXSTALE**, in its own description:

> "Every marker is a FIELD comparison: `RECNO()` and `FOUND()` render EMPTY in a
> '?' marker and `STR()` does not rescue them."

**USE_AGAIN**, generalising after three cuts at one arm:

> "**NO MARKER IN THIS LANGUAGE CAN ASSERT THAT AN AREA IS EMPTY**, and an
> errored marker PRINTS NOTHING rather than going red, so a green count still
> reads full while a claim has silently left the suite."

Both are correct, and both read as quirks of the marker evaluator. Sec 1 gives
the plain reason: **`RECNO` and `FOUND` are not functions in the expression layer
at all.** `RECNO` exists only as a *command* (`src/cli/cmd_recno.cpp`). There is
nothing for `STR()` to rescue.

USE_AGAIN's UA_T4 cost three cuts and a source fix to work around this. That is
the price of the gap being undocumented, paid once already.

## 3. Why it matters beyond the specs

- **A test author cannot discover the boundary.** `HELP FUNCTIONS` lists 73 and
  says nothing about record state; `DELETED` and `RECCOUNT` work but are in no
  catalog, no help topic, and no category. They are learnable only by reading
  `glue_xbase.cpp`.
- **The failure mode is silent.** Per USE_AGAIN, an unresolvable symbol in a `?`
  marker prints nothing rather than going red -- so a spec asserting `RECNO() = 1`
  does not fail, it *disappears*, and the suite still reports green. **An
  undocumented absent function is therefore a silent test-coverage hole, not an
  error.**
- It is the same shape as AIF-079 D1 (declared capability, no consumer) inverted:
  **a live capability with no declaration.**

## 4. Scope -- what I did NOT measure

- Whether `RECNO`/`FOUND` *should* be functions. That is a language decision and
  it is the steward's, not mine. VFP has both; this engine has one as a command.
- Whether any other `glue_xbase.cpp` symbol is surfaced outside the catalog. I
  checked the uppercase string literals in that file and found `DELETED`,
  `RECCOUNT`, plus the `TRUE`/`FALSE` literals at `:63-64`, which are not
  functions. I did **not** audit the other files under `src/cli/expr/` the same
  way.
- Whether the tuple-bound evaluator (`expr_tuple_glue.hpp`) has the same or a
  different set. AIF-074's EVALDIFF harness exists to compare those two
  evaluators and would be the right instrument; it was not run here.

## 5. Options, for the steward

Stated in increasing size. **No recommendation is being smuggled in as a fix.**

1. **Document what already works.** Give `DELETED` and `RECCOUNT` catalog
   entries and help topics. Smallest change; makes two live capabilities
   discoverable and costs no behaviour.
2. **Make the silence loud.** Per USE_AGAIN, an errored marker prints nothing.
   Making an unresolvable symbol in a `?` marker *report* rather than vanish
   would convert every future instance of this class from a silent coverage hole
   into a visible failure. This is the higher-value change and the one with real
   blast radius -- every existing spec would need a green run to confirm nothing
   was silently passing.
3. **Add `RECNO()` / `FOUND()`** as catalog functions. Largest, a language
   decision, and only worth it if 2 shows specs actually want them.

1 and 2 are independent. 2 is worth more than 3 and should be decided first.

## 6. Evidence tier

**Source-evidenced:** sec 1 (both counts re-derived from the registration tables,
cross-checked against the transcript's own `HELP FUNCTIONS` render),
`glue_xbase.cpp:162,172` read directly, `cmd_recno.cpp` present.

**Quoted:** sec 2 -- the IDXSTALE and USE_AGAIN spec descriptions, verbatim from
`REGRESSION LIST`.

**Explicitly unmeasured:** sec 4.

**Chat/AI output:** sec 3, sec 5. No code was written under this note.

## 7. Good Neighbor note

- **What changed.** One new file,
  `docs/maintenance/AIF120_RECORD_STATE_FUNCTION_SURFACE_FINDING_V1.md`.
  **No source file was edited.**
- **Whose area.** Engine, `src/cli/expr/`. Not AIF-120's to change without an
  explicit go.
- **What authorization.** Steward, in session 2026-08-22, asked for a survey of
  commands and functions in HELP against index/order information in `include`
  and `src`. This is the functions half; the index/order half amended R113.
- **How to verify.** Rebuild the catalog list:
  `grep -ho '{\s*"[A-Z][A-Z0-9_]*"' src/cli/expr/fn_*.cpp src/cli/expr/function_catalog.cpp | grep -o '"[^"]*"' | tr -d '"' | sort -u | wc -l`
  -> 73, and `grep -x RECNO` against that list finds nothing. Then read
  `src/cli/expr/glue_xbase.cpp:158-176`. In a shell, `HELP FUNCTIONS` renders the
  same 73.
- **How to undo.** Delete this one file. Nothing else was touched.
