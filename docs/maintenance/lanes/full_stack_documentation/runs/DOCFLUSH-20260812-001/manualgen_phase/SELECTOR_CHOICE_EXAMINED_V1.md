# The selector choice examined -- it is 20, not 21, and neither option is free

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    Lane   : **AIF-068**. No new AIF.
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Status : review-needed. **MEASUREMENT ONLY -- nothing generated, no code
             changed.** Generating command-reference prose remains a
             contract-gated act.

---

## 1. Three things the earlier framing got wrong

`WRITTEN_DEBT_IS_GENERATABLE_V1.md` offered **(a)** pass a narrower
`--baseline-topics` -- "cheapest, but it constructs a baseline to obtain a
result" -- against **(b)** add a second selector, "honest but a code change".
Reading the tool properly changes all three parts of that.

### 1a. It is 20 of 21. TRANSFORM cannot be selected at all.

`supported()` is a HARD filter, and it is not only about the SUPPORTED flag:

    def supported(path):
        return {row["TOPICKEY"]: row for row in read_csv(path)
                if row.get("CATALOG","").upper() == "DOT"
                and row.get("SUPPORTED","").upper() in TRUE_VALUES}

Measured across the 21 in the promoted harvest:

    selectable (a DOT topic, SUPPORTED true)   20   <- all 20 are commands
    NOT selectable                              1   TRANSFORM -- a FUNCTION

**`TRANSFORM` exists only under `CATALOG=FOX`.** Every other one of the 21 has a
`DOT|` topic -- several also carry FOX or EDU rows, which is fine because the
DOT row is what `supported()` keys on.

**Neither (a) nor (b) reaches TRANSFORM -- and they should not.** See 1a-CORRECTED
immediately below: it is a FUNCTION, not a command, and the filter is right.

## 1a-CORRECTED. TRANSFORM is not a command, and the filter was right for a better reason.

Section 1a treated TRANSFORM as a FOX-only COMMAND and posed "does a FOX-only
command get a reference page?" as a third decision. **The owner ran it at the
prompt and the engine answered the question:**

    . transform
    TRANSFORM expects 1..2 argument(s).

That arity is not a command's. It is `TRANSFORM(value, format)`, and it comes
from the expression engine through the **function command-line bridge** -- a
surface the manual already documents under that name.

**TRANSFORM is a FUNCTION.** Its `META_SYSFUNC` row says so in five fields:

    FUNC_ID     FN_TRANSFORM        MIN_ARGS   1      MAX_ARGS  2
    OWNER       expression_engine   FUNC_CAT   Conversion
    SRC_AUTH    function_catalog    VIS_TIER   core
    SRC_FILE    src/cli/expr/fn_string.cpp

`MIN_ARGS 1 / MAX_ARGS 2` is exactly the diagnostic the prompt returned. And
`grep 'registry().add' src` finds **no** TRANSFORM: it is not in the command
registry at all.

**So `supported()`'s `CATALOG == "DOT"` filter excluded it for the RIGHT reason**,
and the Gate 0 envelope already states the principle in its own Q2:

> expression functions are not in the command registry and SYSFUNC owns them.

**There is no third decision. TRANSFORM does not want a command-reference page.**
The question in 1a was one that did not need asking, and one prompt line
dissolved it.

### 1a-i. The general defect: COMMANDS.dbf carries 32 functions

This is not a one-off mislabel. Measured across the whole catalog:

    COMMANDS.dbf distinct names                                    320
    SYSFUNC names                                                   75
    IN BOTH -- function-bridge entries inside the command catalog    32

    ALLTRIM ASC AT ATC CHR CONCAT CTOD DATE DTOC LEFT LEN LOWER LTRIM
    MAX MIN PADC PADL PADR PROPER REPLICATE RIGHT RTRIM SPACE STR
    STRCAT STUFF SUBSTR TIME TRANSFORM TRIM UPPER VAL

**Any count drawn from `COMMANDS.dbf` mixes two surfaces.** That includes counts
this run published:

    "320 distinct command names"     is 288 commands + 32 function-bridge entries
    the 34-name harvest debt          was 33 commands + 1 function (STRCAT)
    the 21 written-debt commands      are 20 commands + 1 function (TRANSFORM)

None of those conclusions changes -- the harvest still needed refreshing, the
pages are still missing -- but **the noun was wrong in each, and "command" was
doing work it had not earned.** Same family as page-existence standing in for
"documented": a column that answers a near-question confidently.

### 1a-ii. And it exposes a debt nobody has counted

    SYSFUNC names                                                75
    linked from functions_and_expression_helpers.md              45
    SYSFUNC names NOT linked from that section                   47

(45 links, 47 unlinked: the section links some names SYSFUNC does not carry.)
TRANSFORM is among the unlinked. **The FUNCTION documentation surface has its own
gap, roughly the size of the command one, and this run flagged "function surface
not measured" three times without measuring it.** It is now measured and it is
not this lane's to fix today -- recorded so the next pass starts from a number.

---

### 1b. (a) is NOT zero-code. The provenance run id is hardcoded.

    page.write_text(_render_page(
        topic, label, selected,
        "DOCFLUSH-20260722-001/help_meta_export_v5",     # <- hardcoded
        "POSTBASELINE_SUPPORTED_COVERAGE_REPAIR"))

`_render_page(topic, label, selected, reference_run, disposition_run)` takes the
run as a PARAMETER; the caller pins it to a July run and a July harvest name.

**A run today from the 2026-08-25 harvest would stamp every page with a run id
that did not produce it.** That is a provenance lie written into 20 pages, and it
is the kind this project has repeatedly refused to accept elsewhere.

**So both options require editing this file.** The argument that (a) is cheaper
because it avoids a code change does not survive contact with the code.

### 1c. The "constructs a baseline to obtain a result" objection is WEAKER than stated

The tool already fails closed on exactly that risk:

    if set(new_gaps) != expected_keys:
        findings.append("EXPECTED_KEY_MISMATCH:actual=...:expected=...")
    ...
    "status": "PASS_CANDIDATE_ONLY" if not findings else "FAIL"
    return 0 if manifest["status"] == "PASS_CANDIDATE_ONLY" else 2

`--expected-topic-key` is repeatable and **the run FAILS unless the selected set
matches the declared set exactly.** An (a)-shaped invocation must therefore name
all twenty keys on the command line, where a reviewer can read them, and any
drift between the baseline and the intent is a hard failure rather than a quiet
difference.

**That is a good guard and it makes either route auditable.** The earlier
objection stands only in this reduced form: (a) still requires FABRICATING an
input artifact -- a topics CSV that excludes the twenty -- and that artifact has
no other purpose and no provenance of its own.

### 1a-iii. CORRECTION to 1a-ii, same day: the 47 was measured against one surface

Section 1a-ii reported "47 SYSFUNC names NOT linked from
`functions_and_expression_helpers.md`" and called it a function DOCUMENTATION
gap. **The count is right and the word was wrong.** The owner ran the engine's
own listings, and functions have four operator-facing surfaces the manual
section is not:

    HELP FUNCTIONS          categorised list, 73 names
    HELP FUNCTION <name>    per-function help
    HELP <category>         NUMERIC, DATE, STRING, SEARCH, LOGICAL,
                            CONSTRUCTION, CONVERSION, MISC
    CMDHELPCHK              Function Inventory -- name, category, MIN, MAX,
                            authority, status, source file

So the 47 is a **manual-linkage** gap, not an undocumented surface. Recorded
correctly rather than left overstated.

### 1a-iv. And the 73-vs-75 gap is ALIASES, not omissions

`HELP FUNCTIONS` totals 21+22+17+4+3+3+3 = **73**; SYSFUNC holds **75**. The two
extra rows are `STRCAT` and `TRIM`, and the first reading here was that an
operator-facing listing was silently dropping two implemented functions --
the AIF-118 shape, and a tidy one.

**The source refutes it:**

    FunctionDoc{ "RTRIM",  { "TRIM" },   FunctionCategory::String, 1, 1, ... }
    FunctionDoc{ "CONCAT", { "STRCAT" }, FunctionCategory::Construction, 1, 32, ... }

The second field is the ALIAS list. **`TRIM` is an alias of `RTRIM`; `STRCAT` is
an alias of `CONCAT`** -- and the catalog says so in its own note, "STRCAT is
treated as an alias of CONCAT". `HELP FUNCTIONS` prints canonical names and
suppresses aliases, **which is correct.** There is no defect.

SYSFUNC marks them, and not by the lowercase category first suspected:

    CONCAT   SRC_AUTH = function_catalog     canonical
    RTRIM    SRC_AUTH = function_catalog     canonical
    STRCAT   SRC_AUTH = builtin_registry     ALIAS
    TRIM     SRC_AUTH = builtin_registry     ALIAS

`STRCAT` carries `MAX_ARGS 32` like `CONCAT`; `TRIM` carries `1,1` like `RTRIM`.

**This is the SAME NOUN PROBLEM as 1a-i, one authority over.** "SYSFUNC has 75
functions" is 73 functions plus 2 alias rows, and the 47 in 1a-ii inherits it.
`SRC_AUTH` is the discriminator and nothing in this run's earlier counts used it.

**One genuine loose end, small:** `CMDHELPCHK`'s Function Inventory prints
`string` in lower case for exactly those two rows while every other String
function prints `String`, and `META_SYSFUNC` stores `String` for all of them.
Two views of one fact disagreeing on case. Noted, not chased.

---

## 2. A risk both options share: the thin topics may FAIL the run

    if not selected:
        findings.append(f"NO_INCLUDED_HELP_ROWS:{key}")

`_deduplicate_lines` classifies each HELP line and keeps only
`INCLUDE_PUBLIC_HELP_EVIDENCE`. A topic whose rows are all excluded produces a
page with no evidence and **fails the whole run**, not just that page.

The three thinnest of the twenty are the candidates:

    TRANSFORM     3 help lines    (already excluded by 1a)
    AVERAGE       6 help lines
    REL_LIST      6 help lines

The other seventeen carry 41 to 161 lines. **This is not predicted, it is
flagged**: whether six raw lines survive classification cannot be known without
running the classifier, and running it is the gated act.

## 3. Recommendation

**(b), and not because (a) is dishonest -- because (a) buys nothing.**

Both routes edit `build_postbaseline_supported_command_pages.py`. (a) additionally
requires manufacturing a baseline topics file whose only purpose is to make a
selector return the answer you already know. (b) states the intent in the
selector itself:

    supported topic, no physical page, regardless of baseline

which is a condition a reader can check against the tree, where "not in the
baseline I handed it" is a condition a reader can only check against an artifact
made for the occasion.

**Concretely, (b) is:**

1. Add a mode -- a flag, not a silent change of meaning -- that selects on
   `slug not in physical_slugs` alone. The existing post-baseline behaviour stays
   the default so the 8-page precedent is not retroactively redefined.
2. Pass the real run id through instead of the hardcoded July string. **Required
   for either option.**
3. Declare all 20 keys via `--expected-topic-key` so the guard does its work.
4. Treat `TRANSFORM` separately, or accept 20 and record why the 21st is out.

**Still gated.** The harvest input contract lists "generating or accepting
command-reference prose from harvested rows" as a separately authorized act, and
that authorization has not been given. Nothing here generates anything.

## 4. What was NOT done

- No code changed, no flag added, no page generated, no tool run.
- `_deduplicate_lines` was read, not executed -- so the thin-topic risk in
  section 2 is identified, not measured.
- No decision taken on TRANSFORM or on whether FOX-only commands are in scope
  for this generator.

## 5. Good Neighbour

    What changed      : this document. Nothing else.
    Whose area        : reports into AIF-068. `tools/manualgen/` was READ, not
                        modified or run; the promoted harvest was read.
    What authorization: the owner's "let us examine the selector choice".
                        Explicitly NOT the contract's prose-generation gate.
    How to verify     : `supported()` at
                        `build_postbaseline_supported_command_pages.py:45`
                        filters `CATALOG == "DOT"`; TRANSFORM's only topic row in
                        `harvested/HELP_HELP_TOPIC.csv` carries `CATALOG=FOX`;
                        the run id at line 96 is a string literal.
    How to undo       : delete this file.
