---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260828-COWORK-001
  recorded_at_utc: 2026-08-28T00:30:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260827-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 1efef54f6
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-27 -- "now give
      me more workspaces, i am glad you found cmd_ersatz.cpp it has good
      features and some work between or work and sqlsel and select
      relationships", then no preference on direction when asked. Authorises
      the measurement and this write-up. The runtime sections come from
      `mcc_topology_workspaces.dts`, written in answer to "now give me more
      workspaces" and run by the owner under X64BASE_ALLOW_DATA=1; it wrote
      five workspace files and no table data. NO code change is authorised by
      this document, and no direction is chosen by it.
  report:
    path: docs/maintenance/AIF147_FINDING_THREE_SURFACES_TWO_CAPABILITIES_AND_ONE_UNREGISTERED_RULE_V1.md
    kind: finding
---

# AIF-147 -- THREE SURFACES DIVIDE TWO CAPABILITIES, AND THE RULE THAT KEEPS THEM APART HAS NO REGISTER ROW

    Number  : AIF-147, claimed 2026-08-28T00:55:30Z with `session_coordinator.py
              claim-aif` (run COWORK-20260827-001, lane
              'relation-traversal-surface-asymmetry'). Claim file verified
              present at `coordination/aif/AIF-147.claim` before the number was
              cited.
              **THIS DOCUMENT BURNED AIF-146 AND THE HOLE IS PERMANENT.** It
              was drafted as AIF-146 before the claim was run, and its intake
              row was written into
              `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- which is
              the allocator's AUTHORITY, not a passive record.
              `session_coordinator.intake_aifs()` reads that file and treats a
              row declaration as RESERVED (`:61-75`), `taken()` unions it with
              the claim files (`:84`), and `next_aif_number()` returns
              `max(used)+1` (`:88-94`). So the draft row reserved 146 against
              itself and the allocator correctly issued 147. No concurrent
              session was involved; an earlier note in this session blamed one,
              wrongly. And 146 cannot be recovered: with the row renamed it is
              no longer in `used`, so `--want 146` is refused as a historical
              gap (`:121-125`) and `--backfill-existing` requires
              `want in used` (`:110`). THE RULE: claim the number BEFORE
              writing it anywhere under `docs/ai-friendly/`, because writing
              into the allocator's input is how you defeat an allocator built
              to prevent exactly this.
    Found   : 2026-08-27, from the owner's observation that there is "some work
              between ERSATZ or WORKSPACE and SQLSEL and select relationships."
              He was right about where the seam is, and it is narrower and
              further along than the phrase suggests.
    Lane    : relational surfaces / SQLSEL / ERSATZ. Adjacent to AIF-074
              (SQLSEL) and AIF-078 (multi-workspace).
    Status  : review-needed. The author does not self-approve, and this
              document deliberately does NOT choose a direction -- when asked,
              the owner expressed no preference, and picking one would be
              deciding R16's fate without a ruling.
    Basis   : MIXED at baseline `1efef54f6`. Every line number was read this
              session. **Sec 3a and sec 6b are RUNTIME-PROVEN** -- run on
              `grimwood` 2026-08-27/28 against the x64 MCC lane
              (`dottalkpp/data/dbf/x64` + `data/indexes/x64`, built by
              `mcc_build_x64.dts`) via
              `dottalkpp/data/scripts/mcc_topology_workspaces.dts`, with every
              prediction written into the script BEFORE the run. Transcript
              excerpts inline. Everything else is source-evidenced. Per
              AIF-145, no development-tree DATA is used as evidence anywhere in
              this document -- the runtime sections assert on OBSERVED ENGINE
              BEHAVIOUR, not on files that happened to be lying about.
    Shape   : Not dead code. A REACHABILITY ASYMMETRY -- a capability in
              production, reached by one surface, declared out of scope by
              another, under a rule with no declared definition.
    Severity: NO DEFECT in the asymmetry itself; it is a design position and a
              defensible one. ONE REAL DEFECT is named in sec 4 (AIF-118
              shape, small, concrete). The finding's value is that it makes
              "the join phase" a decision rather than a project.

## 1. TWO CAPABILITIES

Every relational answer in this engine is built from two independent pieces.

**TRAVERSAL** -- `relations_api::enum_emit_for_current_parent`
(`src/cli/set_relations.hpp:121`, implemented in `src/cli/set_relations.cpp`):

    bool enum_emit_for_current_parent(const std::vector<std::string>& path_children,
                                      std::size_t max_rows,
                                      const std::function<void()>& emit,
                                      std::size_t* rows_emitted = nullptr);

Per its own contract: walks the relation graph from the current parent row,
positions **all involved areas** for each full match, calls `emit()` once per
match, honours `max_rows` (0 = unlimited), and infers a unique single-child
chain when `path_children` is empty. `src/cli/join_engine.cpp` wraps it in a
`WorkAreaCursorRestore` that saves and restores every open area's `recno` and
the starting area, then calls `relations_api::refresh_if_enabled()`.

**This is a working relational join executor, in production.** Not a plan, not
a stub.

**PROJECTION** -- `TUPLE <spec>` (`src/cli/cmd_tuple.cpp:16`), the canonical
tuple builder, with `--HEADER`, `--VALUES-ONLY`, `--AREA-PREFIX`, `--STRICT`.

## 2. THREE SURFACES, AND ONLY ONE COMPOSES BOTH

| surface | traversal | projection | output |
|---|---|---|---|
| `REL JOIN` / `REL ENUM` | **yes** -- `enum_emit_for_current_parent` | **yes** -- `TUPLE <expr>` in the emit callback | rows, one per match |
| `ERSATZ` | **yes** -- relation tree from an inferred root | no | a RENDERING (`TREE`, `GRID`) |
| `SQLSEL` | **refused** | **yes** -- its own select list | rows, single table |

**`REL JOIN` composes them by handing `TUPLE` to the enumerator as the emit
callback** (`src/cli/cmd_relations.cpp:712-729`, `:731-733`). That is the whole
mechanism.

**ERSATZ has the traversal and throws away the rows.** It builds the relation
tree (`browser::relation_build_tree`, `cmd_ersatz.cpp:1092`), infers a best
root when none is set (`infer_best_relation_root_alias`, `:1161`), and computes
incoming counts and depths (`:1117`, `:1132`). Then it renders
(`render_grid_only`, `:1427`). The traversal result is consumed by a display,
never returned as a set.

**SQLSEL has the projection and declines the traversal.**
`src/cli/sqlsel_statement.hpp:16`:

    // Orthogonality (R16): a statement reads the table named in FROM. It does
    // not read or disturb session state -- not the current area, not the
    // record pointer, not SET FILTER, not SET RELATION.

and its own error text (`sqlsel_statement.cpp:190`):

    v1 reads a single table; joins arrive with the join phase.

## 3. THE JOIN PHASE ALREADY ARRIVED, ON A DIFFERENT SURFACE

That is the finding in one line. SQLSEL is waiting for a join engine that
exists, is exercised in production by `REL JOIN` and `REL ENUM`, restores every
cursor it touches, and already accepts an explicit chain.

And SQLSEL is not architecturally isolated from the engine -- **its own header
says the opposite.** `sqlsel_statement.hpp:12-14`:

    The ONE new component of the SQLSEL lane: a SELECT statement parser.
    Everything beneath it consumes proven engine seams (area resolution,
    predicate compile/eval, tuple projection, cursor guards).

It names four shared seams and reaches all four. Traversal is a fifth proven
seam, and it is the one excluded. `sqlsel_statement.cpp:103` even records that
SQLSEL shares its ordering model *with relation equality*:

    // One ordering model, shared with relation equality (R16 orthogonality).

So SQLSEL already shares an ordering model with relations while declining to
read the relations themselves. That is a coherent position -- cursor neutrality
(R16b, `sqlsel_statement.cpp:321`) is real value, and a statement that silently
depended on ambient `SET RELATION` state would be worse than one that refuses
-- but it is a POSITION, and it should be held deliberately rather than by
default.

**R16 has no register row.** Grepped: `R16`, `R16b` and `R16d` are cited in
`src/cli/sqlsel_statement.hpp` and `.cpp` and nowhere else, and
`docs/ai-friendly/R_RULING_REGISTER_V1.md` has no `R16` row. The R-number gate
counts it among the 106 numbers "cited in the tree with no register row." So
**the rule that decides whether SELECT can traverse a workspace's relation
graph exists only as a comment in one header.** Reserved, never reusable, and
undefined. That is the cheapest item in this document to fix and the one most
likely to matter later.

## 3a. RUNTIME-PROVEN: A DOCUMENTED COMMAND FORM IS UNREACHABLE, AND FAILS AS A HELP SCREEN

**This section was found by a mistake, and the mistake is the reason it is
here.** The topology script (sec 6b) called `RELATIONS ALL` to render each
graph. It never rendered one. In all five postures it printed, identically:

    REL syntax
      REL LIST [ALL]
      REL REFRESH
      REL JOIN [LIMIT <n>] [<child1> <child2> ...] TUPLE <expr>
      ...

That is `REL`'s usage block -- a DIFFERENT command's help -- five times, with
no error.

**Cause, read at source.** `cli::preprocess_for_dispatch`
(`src/cli/shell_api_extras.cpp:77-90`) rewrites the line before dispatch:

    // 2) RELATIONS <args...> -> REL <args...>
    if (starts_with_token_ci(line, "RELATIONS", &after_prefix)) {
        return "REL " + line.substr(after_prefix);
    }

So `RELATIONS ALL` becomes `REL ALL`, `ALL` is not a `REL` subcommand, and
`REL` prints its syntax. Meanwhile
`registry().add("RELATIONS", cmd_RELATIONS_LIST)`
(`src/cli/shell_commands.cpp:332`) **can never be reached.** The codebase
already knows: `src/cli/cmd_set.cpp:1984` carries the comment *"before
shell_dispatch runs, so `opt` can never equal "RELATIONS" here."*

**The unreachable form is documented in three places**, which is what makes
this a defect rather than a dead alias:

- `src/cli/cmd_relations.cpp:28` lists `RELATIONS ALL` in the usage block
- `:44` states *"RELATIONS ALL reports a recursive tree rooted at the current
  parent"*
- `include/dotref.hpp:421` publishes `"RELATIONS [USAGE|ALL]"`

And the handler is **fully implemented**: `cmd_RELATIONS_LIST`'s `ALL` branch
(`cmd_relations.cpp:488-511`) calls
`list_tree_for_current_parent(/*recursive=*/true, /*max_depth=*/24)` and
renders the rows. The tree exists. It is simply not reachable by its published
name. `REL LIST ALL` routes to the same handler (`cmd_rel.cpp:117`) and is
presumably the spelling that works; that was not run.

**Two shapes stacked.** AIF-079 -- registered and unreachable; by this lane's
count the ninth instance. And AIF-118 on top of it -- the failure is
INDISTINGUISHABLE FROM A HELP REQUEST. A user who types the documented form
sees a usage block and concludes they mistyped, which is the one reading that
guarantees they never report it. An unknown subcommand printing usage is
ordinarily good manners; here it is what hides the defect.

## 4. THE ONE REAL DEFECT: A CHAIN PARSED, ACCEPTED, AND DISCARDED

`REL JOIN ONE <a> <b> ... TUPLE <expr>`.

`cmd_REL_JOIN` (`src/cli/cmd_relations.cpp:652`) parses the tail into `path`:
`ONE` sets a flag and `continue`s (`:679`), `DISTINCT`/`ALL`/`LIMIT` likewise,
and every other token before `TUPLE` is appended to `path` (`:699`). Then
(`:731`):

    ok = relations_api::join_emit_one_for_current_parent(path, max_rows, emit_row, &emitted);

And `join_emit_one_for_current_parent` (`src/cli/join_engine.cpp:107`) takes it
as:

    const std::vector<std::string>& /*child_chain*/,

The declaration says so too (`set_relations.hpp:100`): *"@param path_children
Optional chain (currently ignored; reserved for future)."*

So the alias chain is **parsed, accepted, and silently discarded.** The command
reports `SetRelationOkText` either way. This is the **AIF-118 shape** -- the
same answer for "applied" and "ignored" -- and the honest forms are already in
this codebase: report the argument as unsupported and refuse, the way
`cmd_list.cpp:538` now refuses an uncompilable FOR predicate (AIF-145 lane,
`7d7b81581`).

**Not claimed:** that anyone is calling it this way, or that `REL JOIN ONE`'s
single-row semantics are wrong. Documented intent is preserved historical
behavior. The defect is the silent acceptance, not the behavior.

## 5. A SMALLER OBSERVATION, NOT A DEFECT

`REL JOIN` (without `ONE`) and `REL ENUM` are **the same function.**
`join_emit_for_current_parent` (`join_engine.cpp:123-131`) is a one-line
delegation to `enum_emit_for_current_parent`, and the file header says why:
*"After the 'true join enumerator' change, REL JOIN delegates to
relations_api::enum_emit_for_current_parent() (same behavior as REL ENUM)."*

Two verbs, one behavior, deliberately and in writing. Recorded because a reader
comparing them will otherwise look for a difference that is not there.

## 6. WHAT THIS MEANS FOR "MORE WORKSPACES"

The owner asked for more workspaces in the same breath as this seam, and the
connection is real: **a workspace is the thing that carries the relation
graph.** A `.dtschema` posture stores areas AND relations; that graph is what
`enum_emit_for_current_parent` walks and what ERSATZ renders.

So "more workspaces" and "select relationships" are one question asked twice:
**what can a workspace's relation graph be used FOR, and by which surfaces.**
Today the answer is: by `REL` for rows, by `ERSATZ` for pictures, and not at
all by `SQLSEL`.

AIF-145 sec 5a is the constraint on any answer: `WORKSPACE SAVE` writes the
WORKSPACES slot and only that, while ERSATZ writes the current-user root, and
ladders 1-3 read the user end first. **Whatever surface is given the relation
graph inherits that split**, so R-a of AIF-145 should be settled before a new
consumer is added to it, or the new consumer joins the disagreement.

## 6b. RUNTIME-PROVEN: WHAT THE TRAVERSAL CONTRACT ACTUALLY DOES

`dottalkpp/data/scripts/mcc_topology_workspaces.dts`, run 2026-08-27/28 on
`grimwood` against the x64 MCC lane. Five workspace postures, one per relation
TOPOLOGY, each with its prediction written into the script before the run --
because the shipped `mcc` posture has a three-way fan at STUDENTS and therefore
can never exercise the inference path at all. It is the hard case only.

**The contract (`set_relations.hpp:121`): when `path_children` is empty, a
unique chain is inferred by "repeatedly following the ONLY child relation at
each step."** Predicted: succeeds on a linear graph, cannot succeed where any
step branches.

    topo_chain   STUDENTS -> ENROLL -> CLASSES -> COURSES -> DEPT
                 bare REL ENUM, no path given -> 5 rows
                 50000000 | S26PHYS210 | PHYS210 | PHYS | PHYS
                 ... PREDICTION HELD

    topo_deep    ... -> CLASSES -> TASSIGN -> TEACHERS -> DEPT   (5 hops)
                 bare REL ENUM, no path given -> 5 rows
                 50000000 | S26PHYS210 | PHYS210 | 100008 | Martin | ARTS
                 ... PREDICTION HELD

    topo_fan     STUDENTS -> ENROLL, STUD_MAJ, MAJORS  (three children)
                 bare REL ENUM, no path given ->
                   REL ENUM engine: enum_emit_for_current_parent failed.
                 ... PREDICTION HELD -- IT REFUSED

    topo_fan     explicit REL ENUM ENROLL -> 4 rows (all of this student's
                 enrolments, not a LIMIT truncation)
                 ... PREDICTION HELD

    topo_diamond explicit REL ENUM STUD_MAJ MAJORS -> 1 row
                 50000000 | CSCI | CSCI

**The finding worth having in writing: the enumerator is HONEST ABOUT
AMBIGUITY.** Given three children and no path, it refused rather than choosing
one. That was the case flagged in the script as *"rows here are a FINDING"*, and
there were none. Any future join surface (sec 7 R-b) inherits a traversal layer
that already declines to guess -- which removes the largest objection to letting
SQLSEL reach it.

**One blemish, and it is the sec 3a shape again in miniature.** The refusal
reads `enum_emit_for_current_parent failed` -- the name of the INTERNAL
FUNCTION, not the reason. Nothing tells the user they have three children and
must name one. It reports WHERE it failed, never WHY, so a correct refusal is
delivered as an internal error.

**And a claim from a neighbouring finding was upgraded by the same run.**
AIF-145 sec 5a argued from source that `WORKSPACE SAVE` writes the WORKSPACES
slot and only that. Five saves, five printed paths:

    WORKSPACE SAVE: wrote D:\code\ccode\dottalkpp\data\workspaces\topo_chain.dtschema
    ... and topo_deep, topo_fan, topo_diamond, topo_flat

all under `data\workspaces`, and `dottalkpp/user/*/workspaces/topo_*` is empty
afterwards. **AIF-145 sec 5a's write-path claim is now runtime-proven** against
this lane. The postures also carry a `WSID F20260828T004514Z` line absent from
the shipped `mcc.dtschema`; noted, not investigated.

## 7. RULINGS OWED

- **R-a.** Declare R16, or withdraw it. It is load-bearing prose in one header
  with no register row. This is owed regardless of every other question here.
- **R-b.** May SQLSEL traverse? Three coherent positions, and the author takes
  none: (i) SQLSEL gains a multi-table FROM that drives
  `enum_emit_for_current_parent`, R16 amended to permit an EXPLICIT chain while
  still forbidding ambient state; (ii) ERSATZ gains a projected set output, so
  the relational browser returns rows and R16 stands untouched; (iii) one
  traversal funnel serves both, the way `compile_where` became the one funnel
  for both evaluator families (AIF-074 ED-01b).
- **R-c.** `REL JOIN ONE`'s discarded chain (sec 4). Refuse it or apply it;
  accepting and ignoring it is the one thing that should not continue.
- **R-d.** Whether `REL JOIN` and `REL ENUM` should remain two spellings of one
  behavior (sec 5). Cosmetic, and it may well be the right answer as it stands.
- **R-e.** `RELATIONS ALL` (sec 3a), RUNTIME-PROVEN unreachable. Three options
  and no preference taken: drop the `RELATIONS -> REL` rewrite so the
  registered handler is reached; teach `REL` an `ALL` subcommand so the
  documented behaviour arrives by the rewritten path; or withdraw
  `RELATIONS ALL` from all three documents and delete the unreachable
  registration. What should NOT continue is a published form answering with
  another command's help.
- **R-f.** The refusal message (sec 6b). `enum_emit_for_current_parent failed`
  names the function, not the reason. Cheap to fix and it is the difference
  between a correct refusal and an apparent internal error.

## 8. WHAT IS NOT CLAIMED

- No claim that any surface is wrong. Each is coherent alone; the finding is
  that two capabilities are split three ways.
- Sections 1 through 6 remain source-evidenced. The run covered the traversal
  CONTRACT (sec 6b) and the `RELATIONS` interception (sec 3a) -- it did not
  exercise SQLSEL, ERSATZ rendering, `REL JOIN ONE`'s discarded chain (sec 4),
  or `REL LIST ALL`, which is the spelling presumed to work.
- The refusal in `topo_fan` is proof that the enumerator declines an ambiguous
  chain THERE. It is not proof that every ambiguous shape is declined.
- No sizing of any option in R-b, and no preference between them.
- No development-tree data of any kind (AIF-145).

## 9. GOOD NEIGHBOUR

    What changed      : nothing. Measurement and write-up only.
    Whose area        : `src/cli/**` is engine and wants an explicit go before
                        any of sec 7 is acted on. SQLSEL is AIF-074's lane;
                        relations and ERSATZ are the workspace lane's.
    What authorization: the owner's request to look at this seam, 2026-08-27,
                        covering measurement and write-up only. He was asked
                        for a direction and expressed no preference, so none is
                        taken here.
    How to verify     : from `D:\code\ccode` --
                        `git grep -n "enum_emit_for_current_parent" -- src include`
                        for sec 1 and 3;
                        `git grep -n "R16" -- src docs` for the missing
                        register row in sec 3;
                        and read `src/cli/join_engine.cpp:107-118` beside
                        `src/cli/cmd_relations.cpp:678-733` for sec 4.
                        For sec 3a, read
                        `src/cli/shell_api_extras.cpp:77-90` beside
                        `src/cli/shell_commands.cpp:332`, then type
                        `RELATIONS ALL` at the prompt with relations set and
                        watch REL's usage appear.
                        For sec 6b, re-run
                        `dottalkpp/data/scripts/mcc_topology_workspaces.dts`
                        -- its predictions are inline and its PROOF block
                        names the five things to read.
    How to undo       : delete this file. It changes no behaviour.
