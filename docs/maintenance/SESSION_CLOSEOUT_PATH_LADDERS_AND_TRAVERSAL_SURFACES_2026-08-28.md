---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260828-COWORK-002
  recorded_at_utc: 2026-08-28T01:20:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: null
    owner: member.derald
    committer: member.derald
  session:
    id: COWORK-20260827-001
    run_id: COWORK-20260827-001
    chat_reference: not_exposed
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: COWORK-20260827-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 891907e858dc029afbe67665a53023e05bb27984
  authorization:
    requested_by: member.derald
    scope: >
      "i wanted you to see that some of these establish dir paths are at
      different levels in the system", then "this system has a gotcha, if you
      have the same artifact at more than one level, which one gets executed
      first, i would think user up" and "do it" for AIF-145; "now give me more
      workspaces ... some work between or work and sqlsel and select
      relationships" for AIF-147, with NO PREFERENCE GIVEN on direction when
      asked; and "lets do it" for this closeout. Three corrections were issued
      mid-flight and are recorded in sec 2. NO code change was authorised and
      none was made.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PATH_LADDERS_AND_TRAVERSAL_SURFACES_2026-08-28.md
    kind: session_closeout
primary_topics:
  - path_resolution
  - multi_workspace
  - relation_traversal
  - sqlsel
  - evidence_quality
  - identity
---

# Session Closeout -- path ladders and traversal surfaces (AIF-145 / AIF-147)

Run `COWORK-20260827-001`, sixth batch. Baseline `891907e85`.
Continues `SESSION_CLOSEOUT_IDENTITY_STAGE1_AND_LIFECYCLE_L1_2026-08-27.md`,
which closed the earlier batches of the same run.

**Two findings claimed, written and committed. No source file was edited.**
Every ruling in both is review-needed; the author does not self-approve.

    41e06ef51  AIF-145: four ladders resolve one workspace name, and the only
               one that obeys SETPATH has no callers
    1efef54f6  AIF-145 amendment: the development tree's data is not evidence
    891907e85  AIF-147: three surfaces divide two capabilities, and the rule
               that keeps them apart has no register row

## 1. THE QUESTION, AND WHY THE ANSWER WAS NOT THE ONE EXPECTED

The owner: *"this system has a gotcha, if you have the same artifact at more
than one level, which one gets executed first, i would think user up."*

His instinct describes three of the four ladders in the tree. It does not
describe the one that runs.

| # | where | rungs, in order | obeys `SETPATH` | reached by |
|---|---|---|---|---|
| 1 | `include/user_scope_paths.hpp:111` | cur, pub, def, slot | slot only | ONE file |
| 2 | `path_state.cpp:468` via `path_resolver.cpp:75` | cur, pub, def, slot | ALL FOUR | **NOTHING** |
| 3 | `cmd_ersatz.cpp:455` | cur, pub, def, data | none | ERSATZ |
| 4 | `cmd_workspace.cpp:690` | **slot, CWD, bare token** | slot only | `WORKSPACE SAVE`/`LOAD`, `catalog_dir()` |

**Ladder 4 has no user rung at all**, and it is the live one for the whole
workspace-catalog lane. **Ladder 2 -- the only one that reads the settable
`cur_/pub_/def_workspaces_root` State fields, and therefore the only one that
could honour `SETPATH CUR_WORKSPACES` -- has zero callers.** That is why the
slot moves nothing observable, and why **L2's affordance is BUILT AND
DISCONNECTED rather than missing.** AIF-079 shape, eighth instance in this lane.

Two rungs also sit ABOVE the user, and one is not a level of the system: a bare
token existing relative to the PROCESS CWD wins, and a token containing any
separator is resolved DATA-relative and **returned even when it does not
exist** (`path_resolver.cpp:103`).

## 2. THE THREE OWNER CORRECTIONS, WHICH ARE THE REAL CONTENT

Each one moved the finding, and each was recorded in it rather than edited out.

**(1) The `tag=none` postures are build stages, not degraded files.** An early
draft read them as degradation lying in wait on rung 2. The owner: *"we include
the mcc.database and a script that hydrates it and then converts it to vfp and
then another x64 schema, then there is a script that builds all of the
indexes."* Chasing that produced the **precise** defect in place of the vague
one: every MCC build stage ends in `WORKSPACE SAVE`
(`mcc_build_x32.dts:309`, `_vfp:279`, `_x64:299`, `_x64_lmdb:303`), which runs
ladder 4's `for_save` branch -- **the WORKSPACES slot and only that** -- while
ERSATZ's `save_ersatz_file` writes the CURRENT-USER root. **Two writers at
opposite ends of one ladder, and ladders 1-3 read the user end first**, so the
build chain's output is the LAST thing they would find, permanently, because no
stage of the chain ever refreshes a user rung.

**(2) The lean staging tree is correct, not a gap.** A draft called the absent
`C:\x64base\dottalkpp\user\` a gap. The owner: *"the staging tree may not be
perfect, but we are trying to stay lean."* User profiles are per-installation
state; shipping a home directory would be the defect. What survived was better:
`ensure_directories()` (`path_state.cpp:490-553`) creates every user, `pub_`,
`def_` and `cur_` root **from the State fields that ladders 1 and 3 never
read** -- so after `SETPATH CUR_WORKSPACES` the directory CREATOR and ladder 2
point at the new location while ladders 1 and 3 keep searching the old one.
R5 in its sharpest form, in the shipped product, with no message.

**(3) The development tree's DATA is not evidence at all.** The owner:
*"don't trust the quality of the data in dev, it has mutated greatly and I
refresh from time to time."* That disqualified a class of measurement the
finding had leaned on, and forced a re-basing onto **source** and **shipped
artifacts** only. **The finding survived unchanged**, because the two-writer
split never rested on dev data -- it rests on source and on the MCC scripts,
which the staging tree confirms ship byte-identical.

**House rule sharpened.** *An empty result is not a measurement* gains a second
form: **a measurement of a mutable working tree is not a measurement of the
system, at any age.** Three admissible sources -- source at a named baseline,
shipped artifacts, and runtime that actually ran with what it ran against
named.

## 3. AIF-147: THE JOIN PHASE ALREADY ARRIVED, ON A DIFFERENT SURFACE

From the owner's *"some work between ERSATZ or WORKSPACE and SQLSEL and select
relationships."* He was right about where the seam is; it is narrower and
further along than the phrase suggests.

Two capabilities -- TRAVERSAL (`enum_emit_for_current_parent`) and PROJECTION
(`TUPLE <spec>`) -- split three ways. `REL JOIN`/`REL ENUM` compose both.
ERSATZ has the traversal and **renders it away**. SQLSEL has the projection and
**refuses the traversal by rule**.

SQLSEL prints *"joins arrive with the join phase"* while the engine it waits
for runs in production under REL, with cursor save/restore. And SQLSEL is not
isolated -- **its own header says the opposite**: everything beneath the parser
*"consumes proven engine seams (area resolution, predicate compile/eval, tuple
projection, cursor guards)"*. Four named, four reached. Traversal is a fifth and
the one excluded. `sqlsel_statement.cpp:103` even records that SQLSEL shares its
**ordering model with relation equality** -- it shares an ordering model with
relations while declining to read them.

**And R16, the rule that decides this, has no register row.** Cited in
`sqlsel_statement.hpp` and `.cpp` and nowhere else. The rule governing whether
SELECT may traverse a workspace's relation graph is a comment in one header.

**No direction was chosen.** The owner was asked and expressed no preference;
picking one would decide R16's fate without a ruling. Six rulings stated, none
preferred.

## 4. WHAT THE RUN PROVED, AND WHAT IT FOUND BY ACCIDENT

`dottalkpp/data/scripts/mcc_topology_workspaces.dts` -- five workspace
postures, one per relation TOPOLOGY, **every prediction written into the script
before the run**. Built because the shipped `mcc` posture has a three-way fan at
STUDENTS and therefore **can never exercise chain inference at all**; it is the
hard case only, with nothing to compare it against.

    topo_chain    linear             bare REL ENUM (no path) -> 5 rows   HELD
    topo_deep     linear, 5 hops     bare REL ENUM (no path) -> 5 rows   HELD
    topo_fan      3 children         bare REL ENUM -> REFUSED            HELD
    topo_fan      explicit ENROLL    -> 4 rows                           HELD
    topo_diamond  two paths          explicit STUD_MAJ MAJORS -> 1 row   HELD

**The enumerator is HONEST ABOUT AMBIGUITY.** Three children and no path, and
it refused rather than choosing one -- the case the script flagged as *"rows
here are a FINDING"*, and there were none. That removes the largest objection to
letting SQLSEL reach it: any future join surface inherits a traversal layer that
already declines to guess.

**AND A SCRIPT LINE THAT WAS WRONG FOUND THE BETTER DEFECT.** The script called
`RELATIONS ALL` to render each graph and never rendered one -- five times it
printed **`REL`'s usage block, a different command's help**, with no error.
`cli::preprocess_for_dispatch` (`shell_api_extras.cpp:77-90`) rewrites
`RELATIONS <args>` to `REL <args>` **before dispatch**, so
`registry().add("RELATIONS", cmd_RELATIONS_LIST)` (`shell_commands.cpp:332`)
**can never be reached**; `cmd_set.cpp:1984` already carries a comment admitting
it. The unreachable form is **documented in three places** and its handler is
**fully implemented** (`cmd_relations.cpp:488-511`). AIF-079 registered-and-
unreachable, **ninth instance**, with AIF-118 stacked on top: **the failure is
indistinguishable from a help request**, so whoever types the documented form
concludes they mistyped -- the one reading that guarantees they never report it.
An unknown subcommand printing usage is ordinarily good manners; here it is what
hides the defect.

**One blemish of the same family:** the refusal reads
`enum_emit_for_current_parent failed` -- the INTERNAL FUNCTION NAME, not the
reason. A correct refusal delivered as an apparent internal error.

**A neighbouring claim was upgraded by the same run.** AIF-145 argued from
source that `WORKSPACE SAVE` writes the WORKSPACES slot and only that. Five
saves, five printed destinations, all `data\workspaces`, user rungs empty
after. Now runtime-proven; AIF-145 amended. The read half remains
source-evidenced.

**And a typo at the prompt confirmed the other half.** `do i_dont_exist.dts`
printed a three-candidate attempts trail with what each resolved to -- the
honest alternative AIF-145 sec 4 holds up, shipping rather than proposed -- and
**not one user rung appears in it**, though `script_search_roots()` puts
cur/pub/def ahead of the slot. The dead ladder, on the script side, printed in
full and passing unremarked.

## 5. THIS SESSION'S OWN ERRORS

**I burned AIF-146 and the hole is permanent.** AIF-147 was drafted as AIF-146
and its intake row was written into `AI_INTERACTION_INTAKE_QUEUE_V1.md` BEFORE
the claim ran. That file is the **allocator's authority**:
`intake_aifs()` treats a row declaration as reserved (`:61-75`), `taken()`
unions it with the claim files (`:84`), `next_aif_number()` returns
`max(used)+1` (`:88-94`). The draft row reserved 146 against itself and the
allocator correctly issued 147. **The rule it cost: claim the number BEFORE
writing it anywhere under `docs/ai-friendly/`.** Writing into the allocator's
input is how you defeat an allocator built to prevent exactly this.

**And I blamed a concurrent session for it, wrongly**, in chat, before
measuring. There was no AIF-146 claim file, no AIF-146 register row, and no
AIF-146 anywhere in the tracked tree -- all three checkable in one command, and
I asserted first.

**I presented AIF-145's core as a new discovery when it is seven days old.**
`AIF120_WORKSPACE_NAME_SHADOWING_REPORT_V1.md` (2026-08-20) already found two
of the four resolvers, measured 27 names with 3 divergent, and named the
`"default"` placeholder. **That report also asked the workspace lane for a
decision that was never recorded** -- older and more actionable than either
finding filed this session.

**A commit message shipped contradicting the document it carried.** `git add`
staged the final files while `git commit -F` read the message file a moment
before I finished rewriting it, so `git log` asserted as fact two things the
document withdrew. Amended in place (`41e06ef51`) because the tip was unpushed.

**A gate prediction was off by one.** I predicted 5 staged paths; the gate
inspected 6, because `TIER0_STATE.md` is a staged path and not a free rider. I
had named it separately and then not counted it.

**A `git add` aborted on a claim file that did not exist**, because I handed
over an add whose claim step had never run. Nothing partial landed -- `git add`
fails as a unit -- but the handover was wrong before it was typed.

## 6. STATE AND WHAT IS OWED

**Nine rulings open** across AIF-145 (R-a..R-d) and AIF-147 (R-a..R-f). The
oldest actionable item is neither: **AIF-120's 2026-08-20 request to the
workspace lane, still unanswered.**

**Not committed, deliberately:** the five generated postures
(`data/workspaces/topo_*.dtschema`) are on disk and reproducible from the script
in one command; committing generated data wants its own ruling. They carry a
`WSID F20260828T004514Z` line absent from the shipped `mcc.dtschema`; noted, not
investigated.

**Noted, not chased:** `mcc_topology_workspaces.dts` was written with LF
endings from a sandbox into a CRLF tree -- git normalises, but the next editor
to touch it will produce a whole-file diff.

## 7. GOOD NEIGHBOUR

    What changed      : two findings, one amendment, one script, this closeout
                        and its Session Log row. NO source file was edited.
    Whose area        : `src/cli/**`, `src/common/**` and `include/**` are
                        engine and want an explicit go before any ruling is
                        acted on. SQLSEL is AIF-074's lane; relations and
                        ERSATZ are the workspace lane's; AIF-120 owns the
                        prior-art report and the decision it asked for.
    What authorization: the owner's in-session direction, 2026-08-27/28,
                        covering measurement, write-up and one fixture script.
                        No direction was chosen on AIF-147 R-b because none was
                        given.
    How to verify     : the commits above; each finding's own sec 9 carries its
                        verification commands; and
                        `dottalkpp/data/scripts/mcc_topology_workspaces.dts`
                        re-runs the whole proof with its predictions inline.
    How to undo       : the findings and this closeout change no behaviour and
                        can be deleted. The script writes five workspace files
                        and nothing else; deleting `data/workspaces/topo_*`
                        undoes its only effect.
