---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-105
  recorded_at_utc: 2026-08-22T04:10:00Z
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
    baseline_commit: 318c6e8c1
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 -- "go",
      taken as the go for R114 option 2 ("make the silence loud"), which I had
      put to him as the highest-value item on the board. Two read-only probes
      were run by the maintainer before any source was edited.
  report:
    path: docs/maintenance/AIF120_MARKER_PREFIX_TRUNCATION_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R115: the value-expression lexers stopped silently, so a PREFIX was returned as the whole expression

Status: **ruling, review-needed. FIXED (3 files). REBUILD REQUIRED.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `318c6e8c1`.

**Area:** engine (`src/cli/expr/`, `src/edu/`). Changed under the maintainer's
explicit go for R114 option 2.

R114 described this behaviour by **quoting two spec descriptions** and filed
both under "Quoted" rather than "Source-evidenced". Measured, they are both
wrong in detail, and the real defect is larger than either.

---

## 1. Measured

Two read-only probes, run by the maintainer 2026-08-22 against STUDENTS
(dbf/x64, 200 records), build at `318c6e8c1`. Scripts kept untracked at
`tmp/r114_marker_probe.dts` and `tmp/r114_marker_probe2.dts`; every value
printed inside `[ ]` so an empty value and a vanished one cannot be confused.

| input (open area) | printed | reading |
|---|---|---|
| `? "[" + "A" + "B" + "]"` | `[AB]` | control |
| `? "[" + UPPER("a") + "]"` | `[A]` | control, known function |
| `? "P1:[" + ALLTRIM("   ") + "]"` | `P1:[]` | an EMPTY value renders as `[]` |
| `? "[" + RECNO() + "]"` | `[` | **truncated. no `]`, no error** |
| `? "[" + RECNO()` | `[` | same -- the tail is not the variable |
| `? RECNO() + "]"` | `FORMULA error: unable to evaluate expression` | loud when the call is FIRST |
| `? "[" + NOSUCHFN() + "]"` | `[` | not specific to RECNO |
| `? "[" + RECNO(1) + "]"` | `[` | not specific to empty parens |
| `? "[" + (RECNO()) + "]"` | `[` | parentheses change nothing |
| `? 100 + RECNO() + 7` | `100` | same in numeric context |
| `? "[" + FOUND() + "]"` | `[` | the other symbol IDXSTALE names |
| `? "[" + UPPER(NOSUCHFIELD) + "]"` | `[NOSUCHFIELD]` | unknown identifier -> its own name |
| `? "[" + RECNO + "]"` | `[RECNO]` | same, bare |
| `? "[" + RECCOUNT + "]"` | `[RECCOUNT]` | **not 200** |
| `? "[" + DELETED + "]"` | `[DELETED]` | **not T/F** |
| `COUNT FOR NOSUCHFIELD = "x"` | `0` | silent |
| `COUNT FOR RECNO() = 1` | `0` | **a count for a clause that never resolved (see 3a)** |

**The mechanism, and it is one line.** `value_eval.cpp`'s value-expression
lexer ends with

    break; // unknown char => stop

and then unconditionally appends `Tok::End`. That subset has **no arithmetic
operators** by design -- its own header comment says so -- so `+` is an unknown
character. The lex stopped at the first `+`, `End` was appended, and the
resulting token stream was **indistinguishable from a complete one**:
`at_end()` returned true on a PREFIX. `eval_string_value_expr` therefore
reported success, and `eval_any`'s step 3 returned that prefix as the value of
the whole expression.

That is why the closing bracket is missing rather than the value being empty,
why the cut is identical for `RECNO()`, `NOSUCHFN()` and `FOUND()`, why
parentheses and arguments make no difference, and why `100 + RECNO() + 7`
prints `100`. When the unknown call comes FIRST there is no valid prefix to
return, which is why that one case was already loud.

`rhs_eval.cpp` carries a second copy of the same lexer with the same bare
`break`. The AIF-074 P1.6 note sitting a few lines above it records this class
biting there once already -- "a dot not followed by a digit ended the lex and
the whole expression silently failed" -- and that repair taught the lexer one
more token instead of teaching it to say when it stopped.

**This is AIF-074 ED-01b, one evaluator over.** `api.cpp:16-27` closed exactly
this shape for the compile_where family: "a predicate whose valid PREFIX parsed
was accepted and its remainder discarded without a word -- the silent
wrong-answer class this lane has now closed four times." It was closed there in
the parser and left open here in the lexer.

## 2. What changed

Three files. **No value that resolves today changes.**

- **`src/cli/expr/value_eval.cpp`** -- `lex_value_expr` takes an optional
  `bool* stopped_early` and sets it at the unknown-character break;
  `eval_string_value_expr` refuses a partially-lexed input. This is what makes
  the existing `at_end()` check mean "the whole input was consumed" instead of
  "the token stream ran out".
- **`src/cli/expr/rhs_eval.cpp`** -- the same change to its copy of the lexer,
  with both callers (`eval_scalar_expr`, `eval_rhs_avalue`) refusing.
- **`src/edu/edu_formula.cpp`** -- the error report now **names the
  expression**: `FORMULA error: <reason> -- in: <expr>`. The `@dottalk.usage`
  block is updated in the same edit, because HELP DATA is mined from it.

The FORMULA change is the half that matters most to the suite. A self-asserting
script carries its marker tag **inside** the expression, so an error printing
only a reason removes the tag from the transcript entirely. Probe 1 printed
`FORMULA error: scalar evaluation failed` twice, for P12 and P13, with nothing
to tell them apart -- which is the precise sense in which USE_AGAIN's "an
errored marker PRINTS NOTHING" was true.

**Expected fallout, and it is the point.** Any expression that was silently
evaluating a prefix now reports. `#` is a common xBase not-equal and neither
lexer knows it, so `FOR LNAME # "X"` -- which has never worked -- will now say
so instead of quietly evaluating `LNAME`. Per the ED-01b precedent: treat a
newly failing script as a bug found, not a regression caused.

Verified: all three TUs pass `g++ -std=c++20 -fsyntax-only` (gcc 11.4, the
device VM). **Not built or run.** A full rebuild and a `REGRESSION ALL` are
owed, and that run is itself the measurement of how much was passing silently.

## 3. Reported, NOT fixed

Each of these is a separate decision and none is inside the R114 option 2 go.

- **The predicate path answers wrong, not just quietly.**
  `COUNT FOR RECNO() = 1` and `COUNT FOR NOSUCHFIELD = "x"` each return 0
  with no diagnostic (but see 3a -- this is not a wrong NUMBER). Two causes:
  `glue_xbase.cpp:178` returns an empty string for a name that is not a field
  (`:198`, `:264`, `:282` are the same site in the numeric accessor and in
  `make_record_view_raw`), and a predicate that fails to COMPILE is swallowed
  by the COUNT path rather than reported. **This is bigger than the marker
  defect** -- a marker that truncates is visible on sight; a `FOR` clause that
  counts 0 looks like an answer.
- **An unknown bare identifier resolves to its own name as a string**
  (`rhs_eval.cpp:849`, `out = make_string(ident)`). A typo'd field name becomes
  data. **Do not simply remove it.** The maintainer flagged the reason during
  this session: bare-word scalars. `DATE`, `TIME`, `NOW`, `TODAY` and
  `DATETIME` are registered with `minArgs 0` (`fn_date.cpp:414-419`) but are
  only reachable in CALL form, so bare `DATE` currently yields the string
  `"DATE"` -- and any change here has to decide what bare `DATE` means before
  it decides what bare `NOSUCHFIELD` means. No tracked `.dts` was found using
  either bare form in a marker; that is a weak negative, not a clearance.
- **The two evaluators disagree, from source.**
  `expr_tuple_glue.hpp:115-135` resolves `RECNO()`, `RECNO`, `DELETED()` and
  `DELETED`, and treats an unknown bare identifier as a string literal;
  `glue_xbase.cpp` resolves none of them. R114 sec 4 parked this as unmeasured.
  AIF-074's EVALDIFF harness exists to compare exactly these two and would be
  the instrument; it was not run here.

## 3a. Correction to this document, 2026-08-22 (steward)

**Steward, in session: "recno() is not a function."** He is right, and sec 3
as first written contradicted R114 sec 1 one document later.

R114 established that `RECNO` is **not a function in this expression layer** --
it exists only as a COMMAND (`src/cli/cmd_recno.cpp`). Sec 3 then described
`COUNT FOR RECNO() = 1` as returning 0 "where the true answer is 1". **There is
no true answer of 1.** The question is not askable in this language, so the
correct response is a REFUSAL, not a count.

The defect is real and the correction sharpens it:

- **Not** "a predicate returns the wrong number".
- **But** "an unanswerable question is answered with a number". `RECNO()` is an
  unresolvable CALL and should report that RECNO is not a function;
  `NOSUCHFIELD` is an unresolvable NAME and should report that no such field
  exists. Both instead produce `0`, which reads as a result.

**This bounds the fix.** Making `RECNO()` evaluate is R114 option 3 -- a
language decision, the steward's, and explicitly out of scope here. The only
change sec 3 argues for is: **stop reporting a count for a clause that never
resolved.** Any patch that makes `COUNT FOR RECNO() = 1` return 1 has answered
a different question than the one this document asked.

Recorded rather than edited away because a shipped ruling asserted something
false, and because the class is this lane's recurring one: I measured a claim
(the count) against an expectation I had invented (that RECNO resolves) instead
of against the finding I had written down four hours earlier.

## 4. Corrections to R114

- **Sec 1 overstated the two live symbols.** `DELETED` and `RECCOUNT` are live
  on the **predicate** path only. From a `?` marker they never reach
  `glue_xbase.cpp` at all -- the identifier-as-literal fallback wins first, and
  probe 2 Q9/Q10 print `[RECCOUNT]` and `[DELETED]`. USE_AGAIN's own
  description said as much ("it serves compile_predicate ... not the '?' marker
  path"); R114 recorded the symbols without carrying that limit into its table.
- **Sec 2's IDXSTALE quote is wrong in detail.** `RECNO()` does not "render
  EMPTY" in a marker; the marker is **truncated at** `RECNO()` and the prefix
  printed. An empty value renders as `[]` (probe 1 P1). The distinction is the
  whole finding.
- **An error of mine in probe 1, recorded because the class is the recurring
  one.** P9 and P11 asserted `(RECCOUNT = RECCOUNT)` and `(DELETED = DELETED)`.
  Those are self-comparisons: the fallback turned both sides into the same
  string literal and `.T.` was returned without either symbol being read. I
  measured something adjacent to the claim. Probe 2 Q9/Q10 are the markers
  those should have been.

## 5. Scope -- what I did NOT measure

- Whether any **other** consumer of the two lexers relied on the prefix
  behaviour. `expand_value_builtins_in_text` passes single call spans, which
  lex completely or already failed the parse; I traced that one and no other.
- The blast radius on `.dts` scripts. Unknown until a `REGRESSION ALL` runs.
- Whether `RECNO`/`FOUND` **should** be functions. Unchanged from R114 sec 4:
  a language decision, and the maintainer's.
- The other files under `src/cli/expr/` were not audited for a third copy of
  this lexer.

## 6. Evidence tier

**Runtime-measured:** sec 1's table, both probes, run by the maintainer
2026-08-22 on his own build at `318c6e8c1`. Transcripts are in-session.

**Source-evidenced:** the mechanism (`value_eval.cpp` unknown-char break and
`End` push; `rhs_eval.cpp`'s copy; `api.cpp:16-27`; `glue_xbase.cpp:178/198/264/282`;
`expr_tuple_glue.hpp:115-135`; `rhs_eval.cpp:849`; `fn_date.cpp:414-419`).

**Compile-verified only:** the change itself -- `-fsyntax-only` on gcc 11.4.
**Not built, not run.**

**Explicitly unmeasured:** sec 5.

## 7. Good Neighbor note

- **What changed.** Three source files -- `src/cli/expr/value_eval.cpp`,
  `src/cli/expr/rhs_eval.cpp`, `src/edu/edu_formula.cpp` -- plus this document.
  No header, no build file, no script. Pre-edit copies are kept untracked at
  `tmp/value_eval.cpp.pre-r115`, `tmp/rhs_eval.cpp.pre-r115`,
  `tmp/edu_formula.cpp.pre-r115`.
- **Whose area.** Engine. Not AIF-120's by default; changed under the
  maintainer's in-session go for R114 option 2 on 2026-08-22.
- **What authorization.** "go", against my stated proposal that option 2 --
  making an unresolvable marker report rather than vanish -- was the highest
  value item on the board.
- **How to verify.** Rebuild, then re-run both probes:
  `DOTSCRIPT D:\code\ccode\tmp\r114_marker_probe2.dts`. Every `[` line in the
  table above should become a `FORMULA error: ... -- in: ...` naming the
  expression. Q0, Q1, Q7, Q8, Q9, Q10 must be UNCHANGED -- they resolve today
  and this change must not touch them. Then `REGRESSION ALL`; any newly red
  spec is a claim that was passing without being evaluated.
- **How to undo.** Restore the three files from the `tmp/*.pre-r115` copies, or
  `git checkout -- src/cli/expr/value_eval.cpp src/cli/expr/rhs_eval.cpp src/edu/edu_formula.cpp`,
  and delete this document. Nothing else was touched.
