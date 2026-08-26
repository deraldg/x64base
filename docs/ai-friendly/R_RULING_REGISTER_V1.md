# R-NUMBER REGISTER V1

**The allocator of record for R-numbers.** Created 2026-08-24 after a near-miss:
a ruling was about to be stamped `R7` on the assumption that each AIF lane
carried its own R1..Rn series. It does not. **The R-space is one flat global
sequence**, and `R7` has been taken since 2026-08-06 -- the owner ruling on
AIF-090 ("CONVERT -- develop and document, it is our thesis").

Nothing detected that. There was no register, no allocator, and no gate; the
number was checked only because someone happened to grep. That is the same
shape this project keeps naming: **a claim that decays without ever going red.**

Run the allocator. Do not pick a number by eye. This file records WHAT each
number means; it deliberately does not record which number is next, because a
document cannot stay correct about that and the tool cannot be wrong about it.

```
$py12 tools\coordination\next_r.py
```

---

## THE ONE RULE THAT SURPRISES PEOPLE

**Doctrine and rulings share the sequence.** `R1` ("derivation runs downward
only"), `R6` ("an absent value must not be representable among present ones")
and `R7` (an owner ruling converting a single lane) are all in the same series.
Two different kinds of thing, one number space.

That was ruled deliberate rather than fixed. Splitting the space retroactively
would renumber citations that are already compiled into code comments, and a
citation that silently means something new is worse than an untidy sequence.
**So the KIND is a column here, not a range.** Read the column; do not infer
the kind from the magnitude.

| kind | meaning |
|---|---|
| `doctrine` | a general rule, expected to be cited far from where it was made |
| `ruling` | a decision about one lane or one artifact |
| `reserved` | cited somewhere in the tree, not yet attributed -- **burned, never reusable** |

**And one marker, which the gate reads:** a row that records what an
ALREADY-PASSED number meant must contain the token **`backfill`**. A row that
ALLOCATES a number now must be above the register's declared high-water and
needs no marker, because taking max+1 *is* the statement. This is the only
thing separating "R7 is a new ruling I just made" from "R7 is what that old
number always meant" -- citation evidence is identical in both cases, so the
human states it once, here.

---

## ALLOCATION RULES

1. **NEXT FREE IS max + 1, NEVER the lowest gap.** Gaps are reported by the
   allocator so a human can rule on them; they are never handed out. A reused
   number makes two decisions share an identity in a permanent record.
2. **A citation burns a number even when nobody can say what it meant.** If
   `R44` appears in the tree and no row here explains it, it is `reserved`, not
   free. You cannot safely reuse a number whose meaning you cannot find.
3. **Padding is display, not identity.** `R095` and `R95` are the SAME number.
   The register's earliest rows are zero-padded and later ones are not; the
   allocator normalises `R0*(\d+)` for exactly this reason. A tool that missed
   it would report a taken number as free -- the AIF-118 shape (the same answer
   for "absent" and "fine") inside the instrument meant to prevent it.
4. **Back-filling a `reserved` row into a real one is always welcome** and
   never changes the number. Mark it `backfill` so the gate can tell it from
   an allocation.
5. **An allocation is above the high-water. A back-fill is at or below it.**
   The gate enforces exactly that and nothing more -- it cannot read meaning,
   so it asks you to declare intent instead of inferring it.

---

## DECLARED

| R | date | kind | lane | ruled by | what it says |
|---|---|---|---|---|---|
| R1 | -- | doctrine (backfill) | AIF-078 | `member.derald` | Derivation runs downward only. |
| R2 | -- | doctrine (backfill) | AIF-078 | `member.derald` | A RUNG needs a PRODUCER, a COMPARATOR and a PERSISTER. |
| R3 | -- | doctrine (backfill) | AIF-078 | `member.derald` | Failure travels in the return value. |
| R5 | -- | doctrine (backfill) | AIF-078 | `member.derald` | One tree, one ladder -- two answers to one question IS the defect. |
| R6 | -- | doctrine (backfill) | AIF-078 | `member.derald` | An absent value must not be representable among present ones. |
| R7 | 2026-08-06 | ruling (backfill) | AIF-090 | `member.derald` | CONVERT -- "develop and document, it is our thesis". Skill programme retired unbuilt after P0 falsified its premise; the four defects P0 found were repaired instead (`79888dfaa`). |
| R110 | -- | ruling (backfill) | AIF-120 | `member.derald` | Workspace path depth: keep `WorkspacePath`, and strike the reason given for keeping it. |
| R112 | -- | ruling (backfill) | AIF-120 | `member.derald` | The measured-zero gate; first-wins-plus-warning admissible ONLY as instrumented behaviour. |
| R113 | -- | ruling (backfill) | AIF-120 | `member.derald` | Order and functions (with R114). |
| R114 | -- | ruling (backfill) | AIF-120 | `member.derald` | Order and functions (with R113). |
| R120 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **The GUI's positional rung IS the engine slot.** Step 3 of the slot lane. The GUI's ordinal was the index into its own area list while the CLI's was the engine slot, so one area had two positional addresses and the posture line `AREA <n>` meant a different thing depending on which surface wrote it. The ordinal is now the slot: sparse, stable across another area's close, and the same number both surfaces print. Costs recorded rather than discovered: the survivor of a close KEEPS its number instead of being renumbered, the vacated slot becomes a hole the next open falls into, and GUI-written postures from before this change carry list indices that will now be read as slots. |
| R124 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **THE RELATION WIRE RECORD LIVES IN `xbase`.** Implementing R122. The posture grammar `RELATION <p> <c> ON <csv> [TO <csv>]` already exists, round-trips, and is held by `dottalkpp_relation_merge_test` -- the format needed no design. The obstacle was PLACEMENT: the formatter is `relation_parse.cpp` in `src/gui`, and `dottalkpp` does not link `dottalk_gui_core`, so the producer could not reach it. Ruled to a neutral home both targets already link, rather than cherry-picked into the CLI (which would invert the dependency direction R122 just ruled and grow the cherry-pick list `area_alloc.hpp` refused to grow on 2026-08-23) or given its own target (correct but ceremony). The unit is std-library-only end to end -- `relation_parse.cpp` -> `relation_parse.hpp` -> `model.hpp` -> `<cstdint> <filesystem> <optional> <string> <vector>` -- and the build ALREADY proves it portable: `src/tests/CMakeLists.txt:43` compiles it into a target that deliberately does not link `dottalk_gui_core`. Same precedent as `area_alloc.hpp` and `workspace_membership.hpp`; `src/xbase` globs its sources so neither consumer needs a build change. |
| R125 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **THE WIRE RECORD CARRIES THE WORKSPACE HANDLE; A NAME IS A RENDERING.** This CLOSES step 2 of `claude/GUI_LAYER_DECISION_OUTLINE.md` -- the NAME-versus-HANDLE seam that has been live since I1.2 partitioned the relation store by handle while the GUI carried a name in six places with nothing converting. The outline asked for the conversion to happen ONCE, IN A NAMED PLACE. The wire record is that place: the producer emits the handle, and a name is produced for DISPLAY by `xbase::workspace::name_of()`, which already exists and which the GUI already calls in exactly one place (`session.cpp:508 owning_workspace_now`). R6 is satisfied by construction and not by a new convention: the handle space already reserves 0 as not-a-legal-handle (`workspace_membership.hpp`, `kDefaultHandle = 1` "precisely so that 0 can mean" absent), so an absent workspace cannot be spelled as a present one. Ruled together with R124 rather than separately, because a record shipped before this was decided would have had a workspace field meaning whatever its first writer put there -- the GUI's existing defect, relocated one layer out. |
| R122 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **`src/gui` DOES NOT DEPEND ON `src/cli`. THE PROCESS BOUNDARY IS THE INTERFACE.** Seam B of `claude/GUI_LAYER_DECISION_OUTLINE.md`, ruled NO. The GUI reaches the engine by SPAWNING a `dottalkpp.exe` (`gui_shell_runtime.cpp:287` CreateProcessW, `gui_cli_bridge.cpp:242` _popen) and parsing its stdout -- there is no in-process command path at all, which the outline did not know when it framed the choice. So the fix for defects 1-4 of its bill (the ` TO ` clause, the posture round trip, the flattened tree, `n/a` becoming a measured `0`) is NOT to link the engine but to make the producer EMIT STRUCTURED DATA across the boundary that already exists, and to consolidate the three parse sites into one DELIBERATE boundary rather than three accidents. B1 was measured and does not collapse -- `set_relations.cpp` takes its engine by injection -- but it costs a `workarea_util` split, a `shell_engine` shim, `command_output` and `db_tuple_stream`, and buys a dependency direction that is hard to walk back. |
| R123 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **THE GUI'S MATCH COUNTER IS DELETED; ABSENT IS SHOWN AS ABSENT.** `count_relation_matches` (`session.cpp`) diverged from `relations_api::match_count_for_child` four ways -- it counted DELETED rows, scanned unbounded, walked physical order instead of the active index, and refused multi-field keys -- so one relation had two match counts and nothing on screen said which one a cell held. Under R122 it cannot be fixed in place: the count is a computation over the GUI's OWN open areas at its OWN cursor positions, which no subprocess can answer without replicating the state. A number that disagrees with the engine is worse than no number. `MaybeMatchCount` and the `n/a` state ALREADY EXIST, so this needs no new type and no link -- R6 was already satisfied and the code was declining to use it. |
| R121 | 2026-08-24 | ruling | AIF-123 | `member.derald` | **ADDRESSING IS ABSOLUTE, TRAVERSAL IS FILTERED.** `GO <n>` names a record and must land on it under any setting: a `GO` that skipped forward would make the one command whose purpose is reaching a specific record unable to reach it, and would close the only door to navigating onto a flagged row to `RECALL` it singly. `SKIP` / `TOP` / `BOTTOM` name a POSITION IN A SET -- next, first, last -- and that set must be the visible one, so they honour `SET DELETED` as they already honoured `SET FILTER`. Ruled on principle and NOT on dialect precedent: the xBase family is honoured but not binding (steward, 2026-08-24), and the only document in the tree answering the `GO` question -- `include/foxpro_go.hpp` -- turned out to be unreviewed generated prose that contradicts itself. The defect was ONE PREDICATE: `navsel::resolve_mode` chose the logical view by asking only whether a SET FILTER was active, so `SET DELETED` -- the second reason the logical view differs from the raw order -- never reached traversal. Everything downstream was already wired. |
| R119 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **`autoq_next` is RESERVED AND UNWIRED.** The x64 header sequence slot stays load-only; the catalog keeps `max(WS_ID)+1` under a FLOCK. Stamped R119 and not R7 because R7 was already taken -- the near-miss that caused this register to exist. |

R4, R8-R109 excluding those above, R111 and R115-R118 are **cited in the tree
and not yet attributed here.** They are reserved by rule 2. Back-fill them as
they are identified; the allocator reports them every run so they do not go
quiet.

---

## RESERVED BY CITATION

**This section deliberately states NO numbers.**

Every `Rnnn` citation anywhere in the scanned tree burns that number, whether or
not a row above explains it. The allocator derives that set on every run. It is
not copied here, and it must not be: a hand-copied population is a hardcoded
denominator, and this project has already paid for one --
`ENTRY_PATH_BASELINE = 127704` in `recall.py`, a frozen number that made a
metric flattering and made the bound written to catch it unable to fire
(AIF-090 D2).

The first draft of this file did exactly that. It stated "highest taken R118,
next free R119" and listed the gaps by hand. **The allocator's first run
contradicted all three claims** -- it found R0, R90, R91, R94, R97, R98, R100,
R104 and R106 cited, which the hand-count had called gaps. The instrument was
right and the document was wrong, roughly ninety seconds after the document was
written. That is the whole argument for deriving it, and it is left here rather
than quietly corrected.

To see the current population:

```
$py12 tools\coordination\next_r.py
```

**A known artifact, stated so nobody re-investigates it:** the scan matches
`\bR0*(\d{1,3})\b`, so `R0` and some low numbers may be incidental text
rather than real citations. They are still burned. Over-reserving costs
integers, which are free; under-reserving costs a collision in a permanent
record, which is not.

---

## GATE

`tools/coordination/r_collision_gate.py`, wired into the pre-push gate beside
the AIF collision gate.

- **HARD:** a duplicate R in the DECLARED table. Two rulings cannot share one
  identity.
- **HARD:** a newly declared number **at or below the register's own declared
  high-water with no `backfill` marker.** That is a decision made now claiming
  a number that has already passed -- the R7 shape exactly.
- **ADVISORY:** numbers cited in the tree with no declared row. There are
  roughly a hundred of these and they predate the register. A gate that blocked
  on them would be switched off within a day -- the same reasoning that keeps
  `check_open_items.py` advisory and that kept `check_aif_claimed.py` to ADDED
  rows only.

**The hard check was wrong twice before it was right, and both are recorded in
the gate's own docstring.** The first cut compared a new number against the
whole working tree, which would have failed the correct flow of declaring and
citing in one change. The second compared against files the change does not
touch -- and blocked this register's own seeding commit, because
**citation cannot separate theft from back-fill at all.** R7-declared-fresh and
R7-declared-historically produce identical evidence. The check was measuring
something that does not carry the answer. Hence the marker: the gate stopped
guessing and asked.

`tools/coordination/test_r_gate.py` -- 11 fixtures, five of which must go red
before their green means anything.

---

**Owner:** `member.derald` -- **steward:** `member.ai.claude.cowork`
**Status:** review-needed. The author does not self-approve.
| R126 | 2026-08-25 | ruling | AIF-128 | `member.derald` | **AN IDENTITY NUMBER IS AN INTEGER; THE ZERO PADDING IS DISPLAY.** Readers match loosely (`AIF-0*(\d+)`, any width, any padding) and normalise to int, so `AIF-43` and `AIF-043` are ONE number; writers keep `%03d`, which is a MINIMUM width and widens by itself past 999; NOTHING in the corpus is re-padded and every existing citation stays valid. Ruled after AIF-128 found `\d{3}` in the collision gate. REJECTED: six-digit padding (answers a display question, costs a rewrite of every citation plus 60 claim filenames, and still needs the loose matcher during any transition) and a real (wrong type for an identity, and there is nowhere to put it -- no DBF has an AIF column; identity needs equality and max() and nothing else). **THE FORMATTER WAS NEVER THE CEILING AND I SAID OTHERWISE:** `%03d` renders 1000 as AIF-1000 quite happily -- the real stop was `AIF_LO, AIF_HI = 6, 999` in session_coordinator, one line from the formatter that had been checked, where `claim-aif` would have returned no candidate at AIF-999. Raised to 999999 with a LAZY candidate generator so the wider bound costs nothing. **NINE READERS MEASURED AGAINST AIF-1000:** seven NO MATCH, one correct (next_aif, which already carried this exact reasoning in a comment and was the only one to have it), and seed_tracking returned `AIF-100` -- not a decline, a DIFFERENT ALREADY-TAKEN NUMBER. The sibling R sequence had the same ceiling and is CLOSER to it (R125 against AIF-128). **THE WIDENING'S OWN FALSE POSITIVE WAS MEASURED, NOT ASSUMED:** widening can only ADD matches, so every newly-matchable token was enumerated -- zero for R across all ten SCAN_DIRS, and exactly one for AIF, which was real. A 2026-08-15 closeout writes `AIF-11{6,7}.claim` as brace shorthand for the PAIR 116 and 117; `{` is a non-word character so `\b` matched `AIF-11` and resolved it to AIF-011. The old pattern missed it BY ACCIDENT; the new one declines it ON PURPOSE via `(?!\{)` on the three PROSE scanners only -- row-anchored patterns need it not, a row id being line-anchored and pipe-followed. **A NEAR-FINDING THE MEASUREMENT REFUTED:** the two allocators do use different rules (next_aif max+1 and never a gap; session_coordinator lowest-free) but `taken()` returns 128 numbers with NO gaps below the high-water mark, so both answer 129 today. Latent, not active; recorded, not filed. Full record `docs/maintenance/R126_IDENTITY_NUMBERS_ARE_INTEGERS_RULING_V1.md`. Ships **review-needed** -- the author does not self-approve. |
| R127 | 2026-08-25 | ruling | AIF-068 | `member.derald` | **WHAT A COMMAND-REFERENCE PAGE IS COMPOSED OF.** Three parts. **(a) CATALOGS: DOT + FOX + UI + DEV compose a developer command page; EDU, EXT, INTERNAL and ED do not** -- they are separate surfaces (`EDU\|BIBLETALK` is 125 lines of lesson material) and are cross-referenced rather than silently dropped. FOX earns its place despite three-line stubs: `FOX\|AVERAGE` carries the full xBase SYNTAX form that `DOT\|AVERAGE` lacks entirely. Asked because the generator keys each page on ONE TOPICKEY while a command's evidence is split across catalogs -- **not two subjects, one command mined twice**: `DOT\|BOOLEAN` cites `edu_boolean.cpp:79 usage_output_block`, `EDU\|BOOLEAN` cites `edu_boolean.cpp:18 usage_contract`, same file, two collectors. Measured: 160 DOT topics have a same-name sibling, 29 have a sibling with MORE lines; BROWSETV would have shipped 3 of 47. **(b) A SOURCE CONTRACT MAKES A COMMAND SUPPORTED -- UNLESS ITS OWN status= SAYS OTHERWISE** (owner: "once a source file has a contract it is supported"). Measured: 215 topics carry `pattern=usage_contract`, 186 marked SUPPORTED, **29 not -- and FIFTEEN of those declare `status=supported` or `supported-conditional` in their own contract while HELP_TOPIC.SUPPORTED says false.** Two answers to one question in one store, the R5 shape; the rule is not policy being imposed, it is the store made to agree with itself. But a contract is not a blanket -- `experimental` (DOT\|TRANSACTION), `sample-extension` (EXT\|STUDENT*), `backend-helper` (EDU\|IDX), `implementation-present` (EDU\|SIX) are the contract's OWN words for not-that. **So the contract makes the MARKER authoritative; the marker, not the contract's presence, decides.** **(c) `developer` IS AN AUDIENCE, NOT A DENIAL OF SUPPORT** (owner: "but that doesn't mean its not dev though"). UI\|BROWSETV, UI\|GENERIC, DEV\|HIER and the four INTERNAL\|*_BUFFER topics all carry contracts and all say developer: supported AND developer, orthogonal axes. A page absorbing a developer-marked sibling must carry that forward -- a developer tool presented as general-audience reference is a worse defect than a thin page. **NOT RULED, AND NAMED AS A DEPENDENCY: the `status=` vocabulary is uncontrolled -- NINETEEN distinct spellings** (supported, supported-conditional, supported-stub-mixed, active, implementation-present, implementation-shim, implementation-helper, dev-tool, developer, dev-canary, experimental, stub, deprecated, deprecated-compat, compatibility-alias, document-control-readonly, backend-helper, sample-extension, review-needed). Part (b) makes that string load-bearing, so it now needs a closed set; separate lane. Also not ruled: whether HELP_TOPIC.SUPPORTED is repaired at source or the contract read at render time. **SCOPE: rule now, apply to the 20** -- the other 26 sibling-richer cases are a measured backlog inheriting the answer; the 191 accepted pages are NOT reopened. **The renderer is NOT touched** -- `_render_page` derives its header from the topic dict it is handed, so composition is the generator's job and `command_reference_candidate.py`, shared with all 191 accepted pages, is unchanged. Full record `docs/maintenance/R127_COMMAND_PAGE_COMPOSITION_RULING_V1.md`. Ships **review-needed**. |
| R128 | 2026-08-26 | ruling | AIF-078 | `member.derald` | **LOAD IS ADDITIVE, AND CLOSE AND SAVE ARE SCOPED TO ONE WORKSPACE.** Opening a workspace no longer closes the one you were in: LOAD from a saved posture and OPEN of a directory both stop being replacement-style, and two directories opened are two workspaces, each holding its own areas. CLOSE and SAVE scope to ONE workspace by default, with an explicit form for everywhere. **THIS ENDS F2 BY DECISION, NOT BY MEASUREMENT.** R110 kept `WorkspacePath` and STRUCK its stated reason because carrier and payload were measured never to coexist -- which held only because LOAD replaced. From here two workspaces can be populated at once on both surfaces, and the type R110 left justified by nothing has its reason back, from THIS decision and not from container nesting (the justification R110 examined and rejected). It also settles the ambiguity `claude/THREE_LANES_INTEGRATION.md` sec 3 left open -- whether the log line `Workspace: mcc_db` named the CATALOG ROW or a RUNTIME HANDLE: **it is both**, a load names the workspace it loads into. **MOST OF THE ENGINE HALF ALREADY SHIPPED** at AIF-078 stage 3: NEW / SWITCH / REGISTRY / DESTROY; bare CLOSE already scoped via `close_workspace_tree` rather than a `MAX_AREA` sweep, so **selective close is done at the CLI**; `WORKSPACE ADD` already additive; `find_free_area_for_workspace` and `join(handle, slot)` already workspace-aware. **AND IT COSTS NO NEW DEPENDENCY:** the whole membership API (`create`, `set_current_handle`, `find_by_name_ci`, `members`, `destroy`) is header-only in `include/xbase/workspace_membership.hpp` and both targets already link `xbase`, so the GUI reaches it without linking the CLI -- **R122 is not touched**, same precedent R124 used for the relation wire record. **FOUR THINGS THIS MAKES WRONG THAT ARE NOT WRONG TODAY.** **(1) SAVE HAS NO WORKSPACE DISCRIMINATOR, AND IT IS LIVE NOW:** `schema_save_to_string()` (`cmd_workspace.cpp:1828`) enumerates `for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0)` with no handle filter anywhere in it. Stage 3 shipped 2026-08-24, so a CLI session can ALREADY hold areas in two workspaces -- which means `WORKSPACE SAVE mcc_db` today writes the other workspace's areas into a posture named `mcc_db`. THE COUNT DISCIPLINE exactly: a number taken from an authority holding more than one KIND with no discriminator applied. The ruling does not create this defect; it removes the last reason it was rarely reached. It is ONE place -- file writer, memo carrier and MINIDB container all pass through that single serializer, so scoping it once scopes all three. **(2) THE GUI CANNOT BE IN A WORKSPACE AT ALL:** `src/gui` reads `xbase::workspace::current_handle()` in three places (`session.cpp:511`, `:577`, `:1664`) and calls `workspace::create` or `set_current_handle` in NONE. So `WS: DEFAULT` on every area after a load is a TRUE report for a stronger reason than sec 3 knew -- not that the load forgot to enter a handle, but that the GUI has no way to be anywhere else. And there are THREE close-all-and-clear sites, not the two sec 4 cited: `session.cpp:1797` (mirror OPEN dir), `:2051` (posture mirror), `:2760` (the Command box `workspace close`). The third closes every GUI area unconditionally while the CLI verb it shadows has been scoped since stage 3 -- two surfaces, one verb name, two meanings. **(3) THE ADDITIVE VERB CANNOT TAKE A DIRECTORY:** `WORKSPACE ADD` is single-table by construction and refuses the case in as many words at `:4851` -- **and the grammar this raised was RULED THE SAME DAY: OPEN ITSELF BECOMES ADDITIVE** (owner: *"open should be additive or it will kill the other workspaces, if a person wants it open by itself then they can close all of the other workspaces first like a sane person"*). Replace is not re-spelled anywhere, it is COMPOSED -- `WORKSPACE CLOSE ALL` then `WORKSPACE OPEN <dir>` -- because **the two mistakes are not equally recoverable**: an additive open the user wanted exclusive costs one extra command, while a replacing open the user wanted additive closes every area in every other workspace unasked, and a dirty one is not recoverable by typing anything. When one error is a keystroke and the other is data, the default belongs on the keystroke side. `ADD` is NOT deleted: OPEN and ADD stop differing in ADDITIVITY (both add) and differ only in GRANULARITY (directory vs one table), which is a better seam -- a verb pair split on *does this destroy your session* is a trap, one split on *how much do you want* is a menu. **A NEW CONSEQUENCE, not ruled:** the second OPEN of an already-open directory. `WORKSPACE NEW` refuses a duplicate name outright (`find_by_name_ci(nm) != 0`, `:4480`), so a second `OPEN` would either refuse or uniquify, and neither is right -- refusing makes a harmless act an error, uniquifying puts two workspaces on one directory. It should RE-ENTER the workspace that directory already has, a second open of the same place being a navigation rather than a creation; what it reconciles in the CONTENTS is the open question. **(4) TWO SURFACES SAY A NAME CANNOT BE RECLAIMED, AND IT CAN:** the header block at `:175-179` and the USAGE output a user actually reads at `:4310-4311` both say there is no DROP verb. Stale since `WORKSPACE DESTROY` landed 2026-08-23 (D10.3, `:4535`, calling `xbase::workspace::destroy` at `:4623`), with `WSL_T4` proving reclamation directly -- destroy `WSLADR1`, create it again, second WS_ID must be GREATER; in-suite 2026-08-24 at 156 -> 157. **And the correction for the line four rows above it DID land:** `:4307-4308` self-corrects the NEW claim and is dated 2026-08-24, so someone walked this exact block that day, fixed one claim and left the DROP claim standing beside it. Third contract drift in the comment block that exists to prevent contract drift, which records the previous two in its own text. Load-bearing, not trivia: under additive open a workspace is created per opened directory, and whether closing one RETIRES it decides whether the second open of the same directory gets a fresh workspace or silently ADOPTS the first one's identity. **NOT RULED, named so they are not settled by drift:** what a second OPEN of an already-open directory reconciles (above); what NAMES a workspace on `OPEN <dir>`, given names must be unique and a directory leaf collides across roots; whether a per-workspace close also DESTROYs; how SAVE spells everywhere (CLOSE's grammar argues `ALL`); relations, still cleared GLOBALLY on a scoped close (`:180`), which additive load makes reach across workspaces routinely rather than rarely; and the UI shape THREE_LANES sec 5 proposed. **NO CODE WAS WRITTEN.** `src/cli/**` and `src/xbase/**` are engine and want an explicit go; `src/gui` waits on the grammar, because the grammar decides what the GUI is mirroring. **NOTHING HERE WAS RUN:** there is no current build on the authoring side, so every claim is source read at HEAD ad34e9145 and none is runtime-proven. Full record `docs/maintenance/R128_ADDITIVE_LOAD_AND_SCOPED_CLOSE_SAVE_RULING_V1.md`. Ships **review-needed** -- the author does not self-approve. |
