# AIF-078 DESIGN -- THE WORKSPACE AS RELATION SUBSTRATE: WHAT ERSATZ, REL AND SQLSEL NEED FROM IT

    Status  : DESIGN, review-needed. NOT a ruling and NOT an implementation.
    Author  : member.ai.claude.cowork (run COWORK-20260827-001)
    Date    : 2026-08-28
    Lane    : AIF-078. Uses the lane's number; no new AIF claimed, because this
              is a design within an existing lane rather than a finding --
              the same convention as
              `AIF078_DESIGN_CATALOG_SPLIT_LEDGER_AND_PAYLOAD_V1.md`.
    Asked by: member.derald, 2026-08-28 -- "back to workspaces, you were
              looking at ersatz, rel, sqlsel (front) for art and integration
              for requirements necessary for their support into our current
              workspace systems integration".
    Basis   : SOURCE-EVIDENCED at `7ef42208e`, plus two RUNTIME facts carried
              from AIF-147 sec 6b and labelled where they appear. Per AIF-145,
              no development-tree DATA is used as evidence.
    Prior   : AIF-145 (four ladders), AIF-147 (three surfaces, two
              capabilities), AIF-120's 2026-08-20 shadowing report and its
              unanswered request, and the SCAN-LIMIT HONESTY regression spec
              registered 2026-08-22 (`src/cli/cmd_regression.cpp:477`).

## 1. THE QUESTION

AIF-147 established that TRAVERSAL and PROJECTION are split across three
surfaces. This document asks the next question, which is the owner's:
**what must the WORKSPACE SYSTEM provide for those three to be supported?**

Not "what should we build." What the substrate has to guarantee before any of
the three can rely on it. Written as requirements so a ruling can accept or
reject them one at a time.

**The headline is that more is already provided than this lane assumed.** Four
of the nine requirements below are MET, two of them deliberately and by design,
and the remaining five are all named in existing findings with existing owners.
There is no new subsystem here.

## 2. WHAT A WORKSPACE ALREADY IS TO THESE SURFACES

A `.dtschema` posture carries AREA lines (dbf, index, indextype, tag, alias)
and RELATION lines (`RELATION <parent> <child> ON <key>`). **The relation graph
is workspace state, saved and restored with the posture.** That is what makes
the workspace -- not the session, not the process -- the thing that defines
what a join may traverse.

## 3. REQUIREMENTS ALREADY MET

**R-1. The relation graph must be scoped to a workspace, not the process.**
**MET, and deliberately.** `src/cli/set_relations.cpp:101-111`:

    static std::unordered_map<std::string, std::vector<Relation>>&
    relations_store_for(std::uint64_t ws) { return all_relation_stores()[ws]; }

    static std::unordered_map<std::string, std::vector<Relation>>&
    relations_store() {
        return relations_store_for(xbase::workspace::current_handle());
    }

The comment on the second says *"the scoping is the whole change"*. Two open
workspaces cannot collide in the relation store. **This is the single largest
prerequisite for multi-workspace, and it is done.**

**R-2. The graph must round-trip through SAVE and LOAD.** **MET, and it
refuses rather than guessing.** `WORKSPACE SAVE` exports through
`relations_api::export_relations()` (`cmd_workspace.cpp:1780`); LOAD
re-establishes through `relations_api::add_relation()` (`:1867`, `:1869`) and
reports every line it will not take -- `! RELATION skipped (bad syntax)`
(`:1824`), `(no fields)` (`:1832`, `:1861`), `! RELATION rejected by engine`
(`:1873`), and `~ RELATION ignored (relations module not present)` (`:2554`).
A posture cannot silently lose an edge on load.

**R-3. Traversal must decline an ambiguous chain rather than guess.**
**MET, RUNTIME-PROVEN** (AIF-147 sec 6b): three children and no path given, and
`enum_emit_for_current_parent` refused. This is the requirement that makes
every option in AIF-147 R-b safe -- a new consumer inherits a traversal layer
that does not invent an answer.

**R-4. A relation must not depend on the child carrying a matching index.**
**MET, and this is the fact that most changes the design.**
`goto_first_match` (`set_relations.cpp:402-438`) does `top()`, then `skip(1)`
in a loop, calling `values_match` on each record. **It never consults an index
or a tag.** So `tag=` on an AREA line is irrelevant to whether a relation
RESOLVES -- a posture with `tag=none` joins exactly as well as one with real
tags. Robust, and see sec 5 for what it costs.

## 4. REQUIREMENTS NOT MET

**R-5. There must be ONE resolver.** AIF-145: four ladders, and the only one
honouring `SETPATH CUR_WORKSPACES` has zero callers. **Any surface given the
relation graph inherits that disagreement**, and a second consumer makes it
harder to settle rather than easier. This is AIF-145 R-a and it should be
decided BEFORE a new consumer is added, not after.

**R-6. An incomplete traversal must announce itself PER RESULT.** **NOT MET,
and the house registered it on 2026-08-22.** `g_scan_limit` is 500,000
(`set_relations.cpp:120`); on reaching it `goto_first_match` calls
`note_scan_truncated()` and **returns `false`** (`:425`) -- which is
indistinguishable from "no matching child". `note_scan_truncated()`
(`:125-131`) is a LATCH: it prints once and every later truncation is silent.
`scan_truncated()` exists to be polled (`set_relations.hpp:37`, whose comment
promises *"consumers may poll scan_truncated() to label results as possibly
incomplete"*) and the SCAN-LIMIT HONESTY spec records that it **has ZERO
POLLERS**. `cmd_rel.cpp:86` clears the latch at the top of each REL command, so
REL gets one warning per command; **anything that does not clear it inherits a
stale `true`, and anything that does not poll it reports a truncated join as a
complete answer.** The spec states the rule this lane should adopt verbatim:
*"an honest incomplete result announces itself, and a silent truncation reads
exactly like a complete answer."*

This is the requirement that matters most for SQLSEL specifically. REL prints
a warning into a transcript a human reads. **A result set does not look like a
transcript** -- it looks complete by construction.

**R-7. The relation graph must be readable by its published name.** AIF-147
sec 3a, runtime-proven: `RELATIONS ALL` is rewritten to `REL ALL` before
dispatch and answers with another command's usage. `REL LIST ALL` reaches
`cmd_RELATIONS_LIST` (`cmd_rel.cpp:117`) and is the spelling that works. A
front surface needs a stable, documented way to ASK the graph what it contains;
today the documented way is the broken one.

**R-8. There must be a stated rule on who may traverse.** R16 governs whether
SQLSEL may read `SET RELATION` and **has no register row** (AIF-147 sec 3).
Requirements cannot be written against an undeclared rule; this is AIF-147 R-a
and it is owed regardless of every other decision here.

**R-9. Traversal must be able to RETURN a result, not only render one.**
ERSATZ builds the tree, infers a root, computes depths and incoming counts --
and then renders (`cmd_ersatz.cpp:1427`). REL composes traversal with `TUPLE`
by handing it an emit callback. **Nothing returns a projected set to a
caller.** Whichever direction AIF-147 R-b takes, some surface has to grow that,
and it is the only genuinely NEW capability in this document.

## 5. THE COST MODEL NOBODY HAS WRITTEN DOWN

R-4's robustness has a price that no document states and no surface reports.

Because `goto_first_match` scans, resolving one parent row against one child is
**O(child records)**. A chain multiplies: `topo_deep` is five hops, so a single
parent row costs the product of the child cardinalities along the chain, capped
per hop at 500,000 steps.

On the MCC corpus this is invisible -- the largest table is ENROLL at 686 rows.
**On a real corpus it is the whole performance story**, and the failure mode is
not slowness but SILENCE: past the cap the scan returns "no match" and, after
the first warning, says nothing.

**Requirement implied:** before any surface offers set-oriented joins to a user
who did not write the traversal by hand, the cost model must be stated and the
truncation must be reportable per result (R-6). A `SELECT` that quietly drops
matches at 500,001 rows is a worse product than one that refuses to run.

Not claimed: that scanning is the wrong choice. It is what makes R-4 true, and
R-4 is why `tag=none` postures work at all. **The defect is the silence, not
the scan.**

## 6. WHAT EACH SURFACE NEEDS, SPECIFICALLY

**ERSATZ** needs R-5 (it resolves through ladder 3, which obeys no `SETPATH`)
and R-9 if its traversal is ever to serve anything but its own renderer. It
needs nothing else -- it already has the graph and walks it correctly.

**REL** needs R-6 and R-7. It is otherwise complete: it composes both
capabilities, it declines ambiguity, and it restores every cursor it touches.
The `REL JOIN ONE` discarded chain (AIF-147 sec 4) is a defect in REL, not a
requirement on the substrate.

**SQLSEL** needs R-8 before anything else, then R-6 with no exceptions, then
R-9 or a way to drive the existing enumerator. It needs R-5 only if a statement
is ever allowed to name a workspace rather than inherit the current one -- and
that question is worth asking early, because `FROM <table>` in a multi-workspace
world is ambiguous in exactly the way `RELATION` was before R-1 scoped it.

## 7. SEQUENCING, PROPOSED AND NOT RULED

1. **R-8** -- declare or withdraw R16. Cheapest, and every other decision reads
   differently depending on it.
2. **R-5** -- AIF-145 R-a, one resolver. Before a new consumer joins the
   disagreement.
3. **R-6** -- give the truncation signal a poller. Independent of both above,
   already specified by the regression spec, and the prerequisite for any
   set-oriented result.
4. **R-7** -- mechanical once R-a is decided.
5. **R-9** -- the only new build, and its shape depends on R-8.

**AIF-120's 2026-08-20 request to the workspace lane is older than all five**
and is about which copy of a workspace wins. It should be answered first
because R-5 is partly a restatement of it.

## 8. WHAT IS NOT CLAIMED

- No sizing, no schedule, and no preference among AIF-147 R-b's three options.
- R-3 is proven for the fan case measured in AIF-147 sec 6b. It is NOT proven
  that every ambiguous shape is declined.
- The cost model in sec 5 is derived from reading `goto_first_match`, not from
  a timing run. No performance measurement was taken.
- `REL LIST ALL` is asserted to work from `cmd_rel.cpp:117` routing to
  `cmd_RELATIONS_LIST`. It was not run.
- Nothing here says the workspace SHOULD become the join's unit of scope. It
  says that if it does, R-1 already put it there and the other five are what
  remain.

## 9. GOOD NEIGHBOUR

    What changed      : nothing. A requirements document.
    Whose area        : AIF-078 owns the workspace lane and this document.
                        SQLSEL is AIF-074's; relations and ERSATZ answer to the
                        workspace lane; R-6 belongs to the SCAN-LIMIT HONESTY
                        spec's owner. `src/cli/**` wants an explicit go before
                        any requirement is acted on.
    What authorization: the owner's request of 2026-08-28, covering
                        requirements only.
    How to verify     : `git grep -n "relations_store_for" -- src` for R-1;
                        read `set_relations.cpp:402-438` whole for R-4 and
                        sec 5; `git grep -n "scan_truncated" -- src include`
                        for R-6, which should return the declaration, the
                        latch, `cmd_rel.cpp:86`, and no pollers.
    How to undo       : delete this file. It changes no behaviour.
