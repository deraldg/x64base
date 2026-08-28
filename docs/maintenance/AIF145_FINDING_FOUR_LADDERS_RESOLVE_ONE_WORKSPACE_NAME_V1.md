---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260827-COWORK-012
  recorded_at_utc: 2026-08-27T23:58:00Z
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
    baseline_commit: 94b626a38
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-27 -- "this
      system has a gotcha, if you have the same artifact at more than one level,
      which one gets executed first, i would think user up", then "do it".
      Authorises the measurement and this write-up. NO code change is
      authorised by this document.
  report:
    path: docs/maintenance/AIF145_FINDING_FOUR_LADDERS_RESOLVE_ONE_WORKSPACE_NAME_V1.md
    kind: finding
---

# AIF-145 -- FOUR LADDERS RESOLVE ONE WORKSPACE NAME, AND THE ONLY ONE THAT OBEYS SETPATH HAS NO CALLERS

    Number  : AIF-145, claimed 2026-08-27 with `session_coordinator.py
              claim-aif` (run COWORK-20260827-001, lane
              'path-resolution-ladder-divergence'). Claim file verified present
              at `coordination/aif/AIF-145.claim` before the number was cited.
    Found   : 2026-08-27, answering the owner's question about precedence
              between levels. The question was better than the answer I had:
              I expected to confirm a ladder and found four of them.
    Lane    : path resolution / multi-workspace lifecycle. Blocks L2.
    Status  : review-needed. The author does not self-approve.
    Basis   : MIXED. Every line number below was read this session at baseline
              `94b626a38`. Sec 5a and sec 6a are FILESYSTEM-MEASURED on
              `grimwood` 2026-08-27/28, and each states its own provenance
              because it is NOT uniform: **sec 5a walks the DEVELOPMENT tree
              only**, sec 6a is the staging tree. No engine was run: the one
              runtime fact (sec 6) is carried from this session's L0 probe and
              labelled where it appears.
    Shape   : R5 -- one tree, four ladders. Aggravated by AIF-079: the ladder
              that is most nearly correct is the one nothing calls.
    Severity: LATENT TODAY, TIMED, AND THE BLAST RADIUS IS NOW MEASURED.
              Sec 5a names the exact files that change content when
              AIF-144 identity normalization lands: six of them, and the
              sharpest is sec 5a: the MCC build chain writes every posture to
              rung 4 while ERSATZ writes rung 1 and ladders 1-3 read rung 1
              first, so a freshly built posture is the LAST thing they find and
              nothing reports it. Sec 6a adds that the directory CREATOR and
              two of the three search ladders can be aimed at different
              directories in the shipped product.

## 0. PRIOR ART, AND A CORRECTION I OWE

**`docs/maintenance/AIF120_WORKSPACE_NAME_SHADOWING_REPORT_V1.md`, 2026-08-20,
already found half of this** and handed it to the workspace lane with a tool.
It measured 27 workspace names, 3 divergent, established that the copy which
WINS resolution is gitignored while the copy that LOSES is the one a clone
gets, and named the `"default"` placeholder as the reason "current-user" and
"default" are the same directory today.

It reported TWO resolvers. This document reports FOUR, and identifies which one
is dead.

The correction: when I first answered the owner's question this session I
presented the divergence as a new discovery. It is seven days old and lives in
this repository. I found the prior art by looking rather than by trusting my own
read, which is the only reason this section exists -- and it is the fifth time
this lane has paid for **a search shaped by the object you have cannot find an
object with a different schema**. That report also asked for a workspace-lane
decision and no decision was recorded. **That open request, not this document,
is the oldest actionable item here.**

## 1. THE FOUR

| # | ladder | rungs, in order | obeys `SETPATH`? | reached by |
|---|---|---|---|---|
| 1 | `include/user_scope_paths.hpp:111` | cur -> pub -> def -> slot | slot rung only | header included by ONE file, `src/cli/extension_manifest.cpp` |
| 2 | `src/common/path_state.cpp:468` via `src/common/path_resolver.cpp:75` | cur -> pub -> def -> slot | **all four rungs** | **NOTHING** -- see sec 3 |
| 3 | `src/cli/cmd_ersatz.cpp:455` | cur -> pub -> def -> data | no rung | ERSATZ only |
| 4 | `src/cli/cmd_workspace.cpp:690` | **slot -> CWD -> bare token** | slot rung only | `WORKSPACE SAVE` / `LOAD` / `catalog_dir()` |

Ladders 1, 2 and 3 are the ladder the owner described: **user up.** Ladder 4 --
the one that runs when you type `WORKSPACE LOAD` -- **has no user rung at all.**

`gui/uidef/resolve_workspace.py` is a fifth transcription of the same question,
but it is honest about being a measuring instrument for ladder 3 and says so in
its own docstring. It is not counted as an authority.

## 2. LADDER 4 HAS NO USER LEVEL

`src/cli/cmd_workspace.cpp:690`, `resolve_workspace_file_path(file, for_save)`.
Read whole, `for_save == false`:

- extension present, path relative: `WORKSPACE_root()/p` if it exists, else
  **`fs::current_path()/p` returned unconditionally**, existing or not;
- no extension: for each of `.dtschema` then `.dtschemas`, try
  `WORKSPACE_root()/probe`, then `fs::current_path()/probe`, then the bare
  `probe`;
- fallthrough: `.dtschema`, `WORKSPACE_root()/p` if it exists, else
  `fs::current_path()/p`.

So the live precedence for the workspace catalog lane is
**WORKSPACES slot -> process working directory -> bare token.**
`user/derald/workspaces` is never consulted, by any spelling, on any branch.

AIF-120's report described this as "relative to DATA only". That was close and
is now superseded: it is the **WORKSPACES slot**, which is settable, and then
the **process CWD**, which is not a level of the system at all.

## 3. THE CORRECT LADDER IS DEAD

`dottalk::paths::resolve_workspace()` and `resolve_script()` are:

- **defined** -- `src/common/path_resolver.cpp:189` and `:207`;
- **declared twice** -- `include/common/path_resolver.hpp:28,31` AND
  `include/cli/path_resolver.hpp:28,31`, same namespace, same signatures;
- **called nowhere.** `grep` for `resolve_workspace(` / `resolve_script(`
  across `src`, `gui`, `include` and `tests` returns their own definitions and
  nothing else. The only other hits are the unrelated Python module named
  `resolve_workspace.py`.

This is the ladder that reads `s.cur_workspaces_root` / `s.pub_` / `s.def_`
from `State` (`src/common/path_state.cpp:468-486`) and is therefore the ONLY
one that would honour `SETPATH CUR_WORKSPACES`. It is the eighth instance this
lane has catalogued of **registered and unreachable** (AIF-079 shape): the
apparatus was built correctly and never wired.

The duplicate header is a second, smaller defect of the same family as AIF-143
(two `cli::Settings`). `diff include/cli/path_resolver.hpp
include/common/path_resolver.hpp` reports only the `subsystem:` tag, a comment
line and trailing whitespace. Ten CLI translation units include the `cli/`
spelling; three include the `common/` spelling. One namespace, one ODR, two
files that may drift.

## 4. TWO RUNGS SIT ABOVE THE USER, AND ONE IS NOT A LEVEL

`src/common/path_resolver.cpp:75-117`, `resolve_in_search_roots`, before any
root in the ladder is tried:

    :84   absolute path that exists -> returned
    :91   bare token that exists RELATIVE TO THE PROCESS CWD -> returned
    :97   token containing any separator -> resolved DATA-relative
    :103     ...and RETURNED EVEN WHEN IT DOES NOT EXIST

Line 103 is the sharp one. A token with a slash in it can never reach a user
level, and when it misses it does not fail as a search -- it fails as a
data-level miss, naming one path, with no trail. `src/cli/cmd_dotscript.cpp:319`
already demonstrates the honest alternative in this same codebase: an attempts
list, every candidate printed with what it resolved to.

The header ladder (`include/user_scope_paths.hpp:135-168`, `resolve_in_roots`)
has the same three pre-rungs with the same ordering.

## 5. THE TIMED HAZARD -- WHY THIS IS AIF-144's PROBLEM

`include/user_scope_paths.hpp:34`:

    inline std::string current_user_name()
    {
        // Replace later with real authenticated user/profile selection.
        return "default";
    }

`src/cli/cmd_ersatz.cpp:392` carries an independent copy of the same
placeholder. So on ladders 1 and 3, **rung 1 and rung 3 are the same
directory**: four rungs, three destinations.

AIF-120 recorded this as "a stated placeholder, not a defect". That was correct
on 2026-08-20 and is no longer the whole picture, because **AIF-144 stage 1 is
in flight and its whole purpose is to make identity real.** The day
`current_user_name()` answers `derald`:

- every artifact that today wins as rung 1 (`user/default/workspaces`) silently
  drops to rung 3;
- `user/derald/workspaces` becomes a live rung above it, and on this machine
  those per-profile sections **exist and are populated but stale since June**
  (measured this session);
- three MCC workspaces whose winning copy is gitignored (AIF-120 sec 1) change
  which file they resolve to, with no message;
- ladder 4 changes nothing at all, so `WORKSPACE LOAD` and ERSATZ diverge
  further rather than converging.

**A behaviour change is hiding inside an identity fix.** AIF-144 named the
WRITE-side version of this -- wiring the resolver to the live actor would make
`catalog_dir()` and `WORKSPACE SAVE` resolve under a different root, so the
catalog would appear to vanish with no error -- and separately warned that
`workspace_search_roots()` is a SEARCH list being asked to choose a WRITE root.
What is new here is the READ-side version: even where nothing is written, rungs
1 and 3 collapse today, so implementing identity re-orders precedence among
per-profile sections that already exist on this machine. Same wire, second
reason not to pull it.

## 5a. TWO WRITERS, TWO DESTINATIONS, AND THE READERS DISAGREE

**Provenance, stated first because it was asked and the answer is not uniform.**
This section reads the **DEVELOPMENT** tree, `D:\code\ccode`, and the scripts
that ship with it. Sec 6a is the staging tree.

**An earlier draft of this section was wrong and is withdrawn.** It read the
1480-byte `tag=none` copies of `mcc.dtschema` as degraded files shadowing good
ones, and warned that `public` -- rung 2 for every profile -- held one. The
owner corrected the premise: the MCC workspaces are **not authored artifacts,
they are generated**, and what ships is a database plus a chain that hydrates
it. In his words: *"we include the mcc.database and a script that hydrates it
and then converts it to vfp and then another x64 schema, then there is a script
that builds all of the indexes."* A `tag=none` posture is not a degraded file.
It is **an earlier stage of the chain**, frozen on a rung nothing refreshes.

`dottalkpp/data/scripts/mcc/README.md` documents the chain and calls it step 5
of user onboarding:

    MyCommunityCollege.zip  ->  dbf/og  ->  dbf/x32 +CNX  ->  dbf/vfp +CNX  ->  dbf/x64 +CDX +LMDB
                                            stage 1          stage 2          stage 3
    then stage 4 (mcc_add_notes_memo.dts) adds the memo columns in place

That reframing does not remove a defect. It replaces a vague one with a precise
one.

**Each build stage ends by saving a posture, and every save goes to the same
rung.** `mcc_build_x32.dts:309`, `mcc_build_vfp.dts:279`,
`mcc_build_x64.dts:299` and `mcc_build_x64_lmdb.dts:303` all end in

    WORKSPACE SAVE <name>

`WORKSPACE SAVE` runs ladder 4's `for_save` branch
(`src/cli/cmd_workspace.cpp:694-698`): a relative name is joined to the
**WORKSPACES slot** and given `.dtschema`. There is no user rung in that branch
and no search. **The build chain writes rung 4, and only rung 4.**

**ERSATZ writes the other end of the ladder.** `save_ersatz_file`
(`src/cli/cmd_ersatz.cpp:846`) resolves its target through
`fallback_in_current_user_root(target, current_user_workspaces_root(), ".erz")`
(`:585`, `:536-549`) -- the **current-user root**. That is rung 1.

So the system has **two writers with two destinations at opposite ends of the
same ladder**, and the readers do not agree which end to prefer:

    writer                          writes to        readers that look there FIRST
    WORKSPACE SAVE (build chain)    rung 4, slot     ladder 4 only
    ERSATZ save                     rung 1, cur      ladders 1, 2, 3

**The consequence: the build chain's output is the LAST thing ladders 1, 2 and
3 would find.** Anything sitting on a user rung shadows a freshly built posture,
permanently, because no stage of the documented chain ever writes or refreshes a
user rung. Re-run the whole hydration and index build, and ERSATZ still resolves
to whatever was on rung 1 before you started. Nothing reports this.

The measurements read correctly once that is understood:

    data/workspaces/mcc_x64.dtschema      13 areas   0 relations   <- stage 3 output
    user/*/workspaces/mcc_x64.dtschema    12 areas  15 relations   <- hand-authored

13 is right and the README says so: `dbf/x64` also holds `TEST64.dbf`, which is
not part of MCC, *"so WORKSPACE reports 13 areas on that lane, not 12."* And 0
relations is right too -- stage 3 does `WORKSPACE OPEN DBF` and saves; it never
sets a relation. **The relations were never part of what the chain produces.**
They are hand-authored, and they live on a rung the chain cannot reach.

The lane already knows this family of hazard. The same README warns:

> Do not use `DO X32` from a script in `scripts\mcc\`. The DOTSCRIPT resolver
> resolves relative to the *invoking script's* directory, so it cannot see
> `data\x32.dts`. It reports the miss and **continues** with the path slots
> unchanged.

A resolver that misses and continues, documented with a workaround rather than
a fix. That is sec 4's shape, found independently by this lane months earlier.

## 6. WHY THIS BLOCKS L2

L2 (isolating regression rows from the production workspace catalog) was
reported blocked because `WSLADDER` / `WSPURGE` write via the WORKSPACES slot
and read via `SET PATH DBF workspaces`. That is this defect in a different
dress: **write through one ladder, read through another.**

`SETPATH WORKSPACES <dir>` does redirect the catalog -- proven this session by
`dottalkpp/data/scripts/l0probe.dts`, which is the one runtime fact in this
document. It works because `catalog_dir()`
(`src/cli/cmd_workspace.cpp:2738-2742`) goes through ladder 4, whose slot rung
IS live. `SETPATH CUR_WORKSPACES` is accepted by the parser
(`src/common/path_state.cpp:369-385`) and stored by `set_slot` (`:285-301`) and
**moves nothing anyone can observe**, because the only ladder that reads it is
the dead one in sec 3.

So the L2 affordance is not missing. It is built, in `path_resolver.cpp`, and
disconnected.

## 6a. THE LEAN STAGING TREE IS CORRECT, AND WHAT IT ACTUALLY SHOWS

**Provenance.** The only section grounded in `C:\x64base`, the publication
staging tree, walked read-only 2026-08-27 with the owner's `tree` listing.

`C:\x64base\dottalkpp\` contains `bin data docs help scripts tools` and no
`user/` directory. **This is deliberate and it is right.** The owner: *"the
staging tree may not be perfect, but we are trying to stay lean."* User profiles
are per-installation state, not publication content. An earlier draft called the
absence a gap; that framing was wrong and is withdrawn.

`data/workspaces` is leaner too -- 50 entries against the dev tree's 56, with
`cmdhelp`, `datadict`, `manuals`, `metadata`, `tmp` and `pk_posture.dtschema`
only in dev. Four files differ (`WORKSPACES.dbf`, `WORKSPACES.dtx`,
`mcc_vfp.dtschema`, `my_custom_workspace.dtschema`); the rest are byte-equal.
The full MCC build chain ships intact and identical -- `data/scripts/mcc/`
(seven files) and `scripts/mcc/` (three) are the same in both trees.

**A second generalization is withdrawn.** An earlier draft said *"what ships is
the zero-relations copy"*, implying loss. It is not loss. **What ships is
exactly what the documented build chain produces**, and the chain does not
produce relations (sec 5a). Whether the shipped MCC demo *should* carry a
relations graph is a workspace-lane decision, and it belongs to AIF-120's
still-open request (sec 8 R-d), not to this document.

**The user rungs are created at runtime, by the authority ladder 2 reads.**
`ensure_directories()` (`src/common/path_state.cpp:490-553`) creates
`s.user_root`, `s.user_public_root`, `s.user_default_root`,
`s.user_current_root` and every `pub_`/`def_`/`cur_` workspaces and scripts
root. A fresh install materialises the whole ladder on first run.

**But it builds them from State fields that two of the three search ladders
never read.** `ensure_directories()` uses `s.cur_workspaces_root`; ladder 2
reads the same field; ladders 1 and 3 recompute from
`data_root.parent_path()`. So after `SETPATH CUR_WORKSPACES <dir>` the
**directory creator and ladder 2 point at the new location while ladders 1 and
3 keep searching the old one** -- in the shipped product, with no message. That
is R5 in its sharpest form, and it needs no staging tree to reach.

**The catalog ships, and it is a snapshot.**

    C:/x64base    .../data/workspaces/WORKSPACES.dbf     75,785 B  2026-08-12
    D:/code/ccode .../data/workspaces/WORKSPACES.dbf    178,423 B  2026-08-27
    C:/x64base    .../data/workspaces/WORKSPACES.dtx  2,844,400 B  2026-08-21
    D:/code/ccode .../data/workspaces/WORKSPACES.dtx  3,125,392 B  2026-08-27

The durable workspace catalog is a publication artifact, fifteen days and 2.35x
behind the development copy. The catalog-split design
(`AIF078_DESIGN_CATALOG_SPLIT_LEDGER_AND_PAYLOAD_V1.md`) and L2 both need that
fact and neither currently states it.

One more same-name-at-two-levels pair, noted and not chased:
`dottalkpp/scripts/{mcc,pinocchio}` and
`dottalkpp/data/scripts/{canaries,main,mcc,messaging,pinocchio}` -- and these
are two halves of one lane, PowerShell drivers in the first and DotScript
stages in the second, not duplicates. `DOTSCRIPT`'s candidate builder
(`src/cli/cmd_dotscript.cpp:287`) tries a bare name, then `scripts/<name>`,
then `tests/<name>`; a second level under `scripts/` is not in that ladder,
which is why the README tells you to inline `SET PATH` instead of `DO X32`.

## 7. WHAT IS NOT CLAIMED

- The full 27-name / 3-divergent census is NOT re-asserted. AIF-120 sec 1
  measured it on 2026-08-20 at `fdacdbfe9` and this session did not re-run the
  census. What sec 5a and sec 6a DO re-measure is the `mcc_x64` and `mcc` cases
  specifically, walked fresh -- because **an old measurement quoted as current
  is not a measurement**. The other 24 names remain on AIF-120's authority.
- No claim that any ladder is wrong in isolation. Each is defensible alone.
  The defect is that four of them answer one question.
- No runtime proof that ladder 1 or 3 ever wins a real resolution on this
  machine. Ladder 1's single consumer (`extension_manifest.cpp`) was not read.

## 8. RULINGS OWED

- **R-a.** Which ladder is the one ladder. The candidates are ladder 2 (already
  correct, needs callers) or ladder 4 (already live, needs a user rung).
  Not the author's call.
- **R-b.** Whether `current_user_name()` may be implemented before R-a lands.
  **This is AIF-144 sec 7 R-b, already open, not a new ruling.** AIF-144
  argued NO on the grounds that the catalog and every posture would resolve
  under a different root and APPEAR TO VANISH. This document supplies a second,
  independent ground for the same NO: sec 5, a silent precedence change among
  per-profile sections that already exist and are already populated. Two
  reasons, one ruling. It should not ride inside an identity commit.
- **R-c.** The duplicate `path_resolver.hpp`. Mechanical once R-a is decided.
- **R-d.** AIF-120's 2026-08-20 request to the workspace lane, still open.
  Older than this document and should be answered first.

## 9. GOOD NEIGHBOUR

    What changed      : nothing. This document is a measurement and a
                        write-up. No source file was edited for it.
    Whose area        : `src/common/**`, `src/cli/**` and `include/**` are
                        engine and want an explicit go before any of sec 8 is
                        acted on. AIF-120 owns the prior-art report; the
                        workspace lane owns the decision it asked for.
    What authorization: the owner's "do it", 2026-08-27, covering measurement
                        and write-up only.
    How to verify     : from `D:\code\ccode` --
                        `git grep -n "resolve_workspace(" -- src include gui tests`
                        should return only the two definitions in
                        `src/common/path_resolver.cpp`. Then
                        `diff include/cli/path_resolver.hpp include/common/path_resolver.hpp`
                        for sec 3, and read
                        `src/cli/cmd_workspace.cpp:690-738` whole for sec 2.
    How to undo       : delete this file. It changes no behaviour.
