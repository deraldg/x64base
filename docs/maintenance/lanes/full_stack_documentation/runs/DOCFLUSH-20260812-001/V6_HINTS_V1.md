# v6 hints -- what the next docpush should not have to rediscover

    Left by   : DOCFLUSH-20260812-001 (flush v5), mid-run
    Steward   : member.ai.claude.cowork
    Owner     : member.derald
    For       : whoever opens flush v6
    Status    : accumulating. v5 is NOT closed; this file is written as the run
                goes rather than at the end, because the two most expensive
                lessons of v5 were BOTH already written down somewhere and not
                found in time.

Lane methodology, in the owner's words: walk the process end to end each pass,
streamline and automate more of it each time, until it is mostly a batch or
chain run. **Each run gets better documented.** This file is that, for v6.

---

## 1. THE ONE THAT COST THE MOST: LEGACY FIRST, AND IT IS NOT A FOOTNOTE

v4 recorded it plainly in its retired-footguns list:

> A dotref.hpp change requires `CMDHELP BUILD LEGACY` then
> `CMDHELP BUILD . <ABS src>` (foxref feeds LEGACY). Back up
> `dottalkpp/data/help` first; the daemon locks the store.

v5 skipped the LEGACY pass anyway, and lost a full cycle to it: the rewritten
dotref entries did not appear in the store, and the steward invented a
"the harvester truncates long summaries" theory to explain it. That theory was
wrong twice over -- the entries were not in the BINARY either, because the
dotref commit had not been made and the exe predated it.

The correct sequence, and v6 should treat it as a gate rather than a note:

    1. COMMIT the dotref/foxref/contract slice
    2. REBUILD the engine            <- dotref is compiled IN; a stale exe
                                        silently publishes the old catalog
    3. back up dottalkpp/data/help
    4. Stop-ScheduledTask DotTalkBBSD   (the daemon locks the store)
    5. CMDHELP BUILD LEGACY
    6. CMDHELP BUILD . <ABS src>
    7. verify with DOTHELP / HELP <verb>, not by grepping the DBFs

Step 7 matters: **grepping the built store cannot attribute a hit to a source**
when dotref and the `@dottalk.usage` contract carry similar wording. It produced
a confident wrong answer in v5. `DOTHELP` renders the compiled dotref catalog
directly and settles it in one line.

## 2. HELP DATA CARRIES NO PROVENANCE -- this is the root cause of section 1

Measured in v5: **zero** commit-sha rows in the store, and `cmdhelp.cpp` records
neither `DOTTALKPP_GIT_SHA` nor the build stamp. Nothing anywhere compares build
time against source mtime.

So the store cannot answer "which binary built me, from which commit, over which
source root?" -- and the only way to check whether it reflects the tree is to
reason about a build. The owner named this exactly: *"you should not have to
hypothetically build."*

Proposed (NOT built, needs the help lane's ruling):

- Stamp provenance rows into HELP DATA at build time: `DOTTALKPP_GIT_SHA`,
  `DOTTALKPP_VERSION_DATE`, build timestamp, mined source root. Gate records
  then bind to their artifact automatically instead of by hand, and a sandbox
  agent reads a row instead of theorising.
- Optional second half: `CMDHELP BUILD` warns when `dotref.hpp` / `foxref.hpp`
  are newer than the running binary's build stamp -- precisely the condition
  that cost v5 a cycle, and the same shape as the stale-exe incident earlier the
  same day (a regression went red because the staged exe predated `FILE()`).

## 3. OPEN: dotref mining, and whether source-level material belongs there

Owner note, 2026-08-12: *"I still need to mine the dotref, we do have some
source at the code level now, I do not know if it needs to be included."*

The question is real and v5 did not settle it. Three surfaces now describe the
same command, and they are separately authored:

1. `dotref.hpp` -- the curated reference entry
2. the `@dottalk.usage` contract block in the command's `.cpp`
3. the `HELP <verb>` topic renderer, which has its OWN third wording

Measured in v5's Gate 2 transcript: all three render `WORKSPACE` differently in
a single build. `refcheck` proves every dotref entry RESOLVES to a command; it
does NOT prove the three descriptions AGREE, and nothing else does either.

AIF-067 M2 is chartered as "flag dotref summaries that drifted from the
contract" -- which covers (1) vs (2). **Recommend v6 extend that scope to (3)**,
because the topic renderer is what an operator actually reads.

Related, and unresolved: if dotref is to be mined FROM the contracts, then much
of what v5 hand-wrote into dotref duplicates the contract by construction. If
dotref is instead a curated human-facing layer, the duplication is deliberate
and the drift check is the answer. That is a lane-shape decision, not a task.

## 4. OPEN: expression functions are publishing as unsupported COMMANDS

Found in v5's LEGACY output. Five functions carry an uncurated DOT command row:

    460 DOT FILE       "... is a registered DotTalk++ command; curated DOTREF
    456 DOT UDATE       support status and help summary are pending."
    457 DOT UDATETIME   (all five: supported=no)
    461 DOT UTIME
    462 DOT UNOW

All five are simultaneously in the Function Inventory. Two tools disagree:

- `cmdhelp.cpp` has `is_expression_function_name()` specifically to prevent this
  ("Expression/function names are reflected through the function catalog, not as
  unsupported DOT command placeholders") -- and it is not catching them.
- `dotref_autogen.py` asserts they cannot appear at all: "expression functions
  (function_catalog.cpp, e.g. the U* = DATE("UTC") family) are NOT in the
  registry, so they never appear here -- SYSFUNC owns them."

The complication, and it is genuine rather than a bug: **catalog functions ARE
invocable as scalar commands** -- `DATE`, `LEFT "hello", 2`, `FILE "path"` all
work at the prompt, no parens. So the command/function boundary is really blurry
here, not simply broken. Three candidate rulings for v6:

  (a) curate them in dotref as dual command+function;
  (b) fix the filter so they stay function-only and HELP stops publishing them
      as unsupported;
  (c) accept that the scalar form means every catalog function has a command
      surface, and decide what that implies for the catalog as a whole.

`FILE` is the newest instance (added 2026-08-12), so whatever is decided will
apply to the next function added too.

## 5. OPEN: harvest scope, 205 mined vs 229 present

The v5 ad-hoc build reported "3459 row(s) from 205 file(s)". Measured the same
day:

    contract-bearing .cpp             229
    contract-bearing .cpp + .hpp      233
    contract-bearing .cpp in src/cli  203

205 is close to `src/cli` (203), not to the tree (229). If the harvest is
`src/cli`-shaped, then `src/edu/*` (16 contract files), plus contracts under
`src/help`, `src/identity`, `src/xbase` and `src/security`, are not mined at
all -- a silent coverage gap in the authority the whole flush reconciles
against.

Not asserted as a defect: the 2-file gap between 203 and 205 is unexplained
either way, and the miner may take an explicit root list. **v6 Phase 1 should
determine which**, because "contracts exist" and "contracts are harvested" are
different claims and only the second reaches HELP.

Confirmed while forming the question, so v6 need not re-derive it: `edu_` and
`app_` handlers ARE native commands belonging in dotref (`dotref_autogen.py`
routing: `cmd_` / `edu_` / `app_` -> NATIVE). `lab_` does not exist as a prefix.
`edref` is a separate catalog owning its own namespace.

## 5a. The pre-MINIDB workflow still works, and is MORE exposed to the new gate

Asked and answered on 2026-08-12: **can a workspace still be saved to a memo as
a plain v2 posture, the way it worked before the container carried table bytes?**

Yes, and it is still the DEFAULT -- `int ver = 2` in the dispatcher; only a
trailing `V3` or `MINIDB` moves off it. Proven post-change the same day:
`WORKSPACE_MEMO` uses exactly `WORKSPACE SAVE wm_regress MEMO` /
`WORKSPACE LOAD wm_regress MEMO` (43 areas, 58 relations) and ran 4/4 green
after the load-shortfall refusal landed.

**The interaction worth knowing, because v2 is more exposed than v3.** The new
LOAD refusal applies to every carrier. A v2 posture carries no DBFROOT, so it
resolves against whatever environment is currently set -- which is exactly the
case that used to half-load and now ABORTS. Same posture, same wrong
environment: v3 finds its tables anyway because it carries its own address;
**v2 will refuse where it previously restored what it could.** `PARTIAL`
restores the old behaviour explicitly. Not a regression in the v2 path -- the
new gate meeting the older format's looser guarantee.

## 5b. A naming decision, recorded because the reasoning outlives it

Proposed: call a v2 posture carried in a memo **"DTSHEMA 2.5"**. **Rejected**,
and the reason generalises.

A v2 posture is BYTE-IDENTICAL in a file and in a memo apart from its WSID line.
The code keeps the axes deliberately orthogonal -- "the FORMAT is identical
across carriers; the INSTANCE is identified" -- so a 2.5 would have announced a
byte difference that does not exist, in a namespace that has already cost one
reconciliation (the DTSHEMA-name collision, AIF-078 D5/Q5 -> DTWSSNAP 1).

The site had already solved it correctly, which is why checking mattered:
`/docs/engine/ecosystem-feature-comparison` names these as CAPABILITIES with
format as an attribute -- "Workspace stored *inside* a database table", "Self-
locating snapshot ... Yes, format v3" -- never as the row's identity.

What the proposal was really reaching for was VISIBILITY: nothing at the prompt
told an operator which saved rows carry their tables. Answered by
`WORKSPACE CATALOG` (2026-08-12), which surfaces FMT -- posture vs table bytes
-- plus size, areas, author and which rows are superseded.

General rule for v6: **when a version number is proposed, check whether the
distinction is a payload difference or a placement difference.** Only the first
belongs in a format namespace.

### 5c. The correction the first run produced, and why it is a pattern

`WORKSPACE CATALOG` shipped with a **CARRIER column, and its first live run
printed `-` for all 106 rows.** Both mistakes are worth carrying forward:

1. It read the catalog's `WS_ID`, which is `N("WS_ID", 10)` -- NUMERIC, never
   held a letter. The `M`/`F` prefix lives in the **WSID line inside the
   payload** (`stamp_ws_id`). Two different things share the name "WSID", and
   the design reasoning slid between them without anyone noticing.
2. **Even corrected it would have been a constant.** `save_to_memo` holds the
   only `appendBlank()` against `WORKSPACES.dbf`, so a catalogued row IS a memo
   row by construction. A column that can only take one value is not a column.

The second is the reusable one: **before adding a column, ask what would have
to be true for it to hold a different value.** If nothing in the writer can
produce one, the fact belongs in the footer, not the table.

The fix also found something the column was groping at and missing -- the FILE
carrier is not in the catalog AT ALL. Those are `.dtschema` files sitting in
the same directory, invisible to every catalog query. The report now counts
them so the table does not read as the whole inventory.

**v6 process note:** this defect survived a syntax check, a documentation pass
across four surfaces, and a full pre-commit gate. Nothing available at commit
time could have caught it, because every gate checks *consistency*, not
*correspondence with data*. The first RUN caught it immediately. Recorded here
because the lane's habit is to treat a clean gate as sufficient, and for a
report over live data it is not -- **a report is not proven by compiling; it is
proven by pointing it at rows.**

## 6. SETTLED IN v5 -- do not re-derive these

- **Contract-block ASCII is clean.** 0 non-ASCII inside any `@dottalk.usage`
  block, tree-wide, measured after the sweep in `4c584ba8f` (215 replacements,
  141 files). v4's proven mojibake case (`cmd_buildvectors.cpp:21`) is fixed and
  v5's Gate 2 transcript is garble-free.
- **The enforceable rule is narrower than the task's wording.** Not "no
  non-ASCII in comments" -- the harvester reads the CONTRACT BLOCK only. Proof:
  `U+2500` box-drawing appears 3556 times inside comments in contract-bearing
  files and **0 times** in built HELP DATA. So a gate can check contract blocks
  precisely without touching 3556 decorative separators or the 312 accented
  characters the localized surfaces need (0 of which are in comments -- they are
  all runtime strings).
- **`risk:` blocks are NOT harvested.** VDISK's long-standing
  `loses_ephemeral_data` scores 0 in the store, as do all risk keys. A `risk:`
  block is for source readers today. Whether it SHOULD reach HELP is a lane
  question; recorded so nobody writes more expecting them to surface.
- **STILL OPEN from AIF-088:** the whole-file gate on contract blocks.
  `check_house_style.py` still has `CHECKED_SUFFIXES = (".md",)`, so the rule
  ("no em-dashes in scripts or docs") remains wider than its enforcement.

## 7. Process note, offered against this steward's own record

Twice in v5 the steward presented a finding as new that was already written
down: the house-style gate gap and the ASCII sweep were BOTH recorded in
`labtalk/registries/ai_portal_tasks.yaml` on 2026-08-05, with the same analysis
and the same prescription. The owner had already said where the evidence lived.

**Cheapest possible check before claiming a discovery:** grep
`ai_portal_tasks.yaml` and the lane's own `runs/*/NEXT_PUSH_CONTINUATION*` for
the subject. Both are small. Both were right.

---

## 8. v6 STARTS BY RUNNING TWO COMMANDS. That is the whole improvement.

    Added 2026-08-25, run COWORK-20260824-001, at the owner's instruction
    ("make sure fullstack doc push v6 goes much smoother").

Sections 1 through 7 are prose, and prose is what v5 kept failing to read in
time. Section 1 opens by admitting the lesson was already written down and lost
anyway. So the answer is not a better warning. **It is a check that runs.**

    $py12 tools\fullstack_docs\docpush_preflight.py --root . <- before you start
    $py12 tools\fullstack_docs\docpush_preflight.py --root . <- after every rebuild

That is the gate -- **the one that has existed since 2026-08-05**, now carrying
five checks instead of three. It takes about a second, reads only file times and DBF
headers, needs no engine and no build, and runs in a sandbox that cannot
compile -- which is where most of this lane's verification actually happens.

### 8a. What it checks, and which cycle each one cost

Every check is a failure that ACTUALLY HAPPENED, and every one of them produced
output that looked correct at the time.

| check | the failure it encodes | when |
|---|---|---|
| `binding` | exe built from a dirty worktree, so the store is not reproducible from any commit | 2026-08-24 |
| `exe newer than catalogs` | dotref/foxref are COMPILED IN; a stale exe silently publishes the old catalog | 2026-08-12, section 1 |
| `store newer than exe` | store rebuilt by an exe that predates the change under test | 2026-08-12 |
| `legacy before store` | `BUILD LEGACY` and `BUILD . <src>` passed as ONE array; only the first ran | 2026-08-24 |
| `generation stamp` | the two tables generated on different days -- one rebuild reached only one | -- |
| `store integrity` | 2,757 rows with a blank `TOPICKEY`, invisible for five rebuilds | AIF-126 |
| `status coherence` | 167 rows that are `pending` and `AUTHORITATIVE` at once | open |

Steps 1 to 3 of the preflight (contract coverage, catalog drift, plan ASCII)
were already there and are unchanged. Steps 4 and 5 are the table above.
**Steps 1-3 check CONTENT. Steps 4-5 check ORDER and the join. Neither half can
see the other's failures**, which is why v5 passed 1-3 while losing cycles to 4.

All seven detectors were tested against real evidence before this was written:
the pre-fix store (`help.bak-20260824-175951`) fires `store newer than exe` and
`store integrity`; a synthetic half-run fires `legacy before store`; and a
same-second rebuild does NOT fire it, so the tolerance is not a false positive
waiting to happen. A gate nobody has watched fail is not a gate.

### 8b. THE RULE THAT COST THE MOST THIS PASS

**One `datarun.ps1` invocation per HELP-mutating command. Never an array.**

Section 7 of `help_refresh/HELP_REFRESH_PACKAGE_V1.md` reads "5 + 6" and passes
both builds in one `-CommandLines` array. **Split it.** `--script` is stdin
redirection (`main.cpp:195-213`), so a nested `std::cin` read inside the first
command eats the following line and the second never runs. It cost v5 a cycle on
2026-08-12, and on 2026-08-24 it happened AGAIN inside an apply script written
by the same steward who had just documented it -- because the form was copied
from the package without being questioned.

The transcript of a half-run is complete, well-formed, and wrong. Only the
clock catches it. That is now `legacy before store`.

### 8c. Two Gate 4 assertions v6 should adopt, and one it should retire

**Adopt 1' -- provenance, replacing the withdrawn build-stamp assertion.**
The banner has carried the answer all along:

    dottalk++ v0.6 (2026-08-24, c39d966c dirty)  (Aug 24 2026 17:05:41)

Commit AND dirty flag. The assertion is: **the banner names a commit and is not
`dirty`.** One grep. It is the only assertion in the set that can catch the
2026-08-12 failure, and `docpush_preflight` checks the same fact from git.

**Adopt 6' -- a topic-SET diff, retiring the topic-count floor.**
On 2026-08-24 the count floor scored a REPAIR as a regression: five expression
functions correctly stopped being invented as commands, the total fell from 530
to 526, and assertion 6 failed. A floor cannot tell content lost from
miscategorised content correctly removed. The replacement names every departure
and lets a human disposition it:

    $py12 tools\coordination\help_store_check.py --against <pre-run store>

The LINE floor may stand -- lines are additive, and a fall there is real signal.

**Retire 5b entirely.** It was withdrawn as malformed in v5 and should not
reappear: an `EDREF` HELP_LINE row count cannot witness a change that lands in
`HELP_TOPIC.TITLE`.

### 8d. The family all three withdrawn assertions belong to

The build stamp, the EDREF row count, and the topic floor failed the same way:
**a proxy that cannot answer the question put to it.** `__DATE__` in a
translation unit that need not recompile cannot witness freshness. A row count in
one table cannot witness a change in another. A total cannot witness membership.

Before writing an assertion, ask what OTHER world would produce the same number.
If the answer is "a healthy one" or "a broken one", the assertion is not
measuring what it claims. Three of eight failed this test in v5.

### 8e. Before calling anything a discovery

    $py12 tools\coordination\docpush_preflight.py --prior-art "<subject>"

Searches `ai_portal_tasks.yaml`, every `NEXT_PUSH_CONTINUATION*`, and this file.
Section 7 recorded that twice in v5 a "finding" was already on record with the
same analysis and the same prescription. This is that check, automated. Run on
"em-dash" it returns five hits immediately -- including the two that were missed.

### 8e2. A TEST IN ANOTHER LANGUAGE IS A PROXY TOO

2026-08-25. The owner ruled a 256-character preview column. I implemented it,
then verified the boundary logic by porting it to Python and running six cases.
All six passed. The change was still broken: a dBase III field-length
descriptor is ONE BYTE, `256` wrapped to `0`, and the build wrote a ZERO-WIDTH
column that reduced all 500 summaries to nothing.

**Python integers do not wrap. My test could not have found it, and I presented
it as verification anyway.** MSVC did find it -- C4305 and C4309, at compile
time, pointing at the exact argument -- and the OWNER read the warnings while I
was busy trusting my test.

Two rules out of it:

- **Read the compiler's warnings before reporting a change as verified.** They
  are a second reviewer that already ran.
- **A test written in a different language than the code tests a different
  program.** Fine for algorithm shape; useless for overflow, width, signedness
  or anything the type system decides. Know which one you are checking.

This is section 8d's family again -- a proxy that cannot answer the question put
to it -- and it is the first one this steward COMMITTED rather than merely
wrote a warning about. Three withdrawn Gate 4 assertions, then this.

### 8f. Before writing what a defect COSTS, read a row

AIF-126 was measured correctly and then described wrongly. The finding said nine
percent of the help store was unreachable by any operator and named `SET` and
`ABOUT` as the headline losses -- which reads as missing SET documentation. One
sample row refuted it: the payload is the runtime MESSAGE CATALOG, `{placeholder}`
templates that `CMDHELP` excludes from rendering on purpose. The true figure is
530 operator-facing rows across 83 topics. Real, and much smaller.

**The measurement was sound and the sentence about it was not.** Sampling one
row costs nothing and would have caught it. A correct number does not license a
claim about what the number means.

### 8g. An item is "blocked" only when someone has tried it and been stopped

Five blockers went into the 2026-08-24 triage. **Two had been answerable for
three passes and had simply never been attempted** -- a direct `HELP_TOPIC.TITLE`
read (settled in one command), and `FN_COVERAGE`, which is not a dotscript verb
at all but a metacollect check whose output was already sitting in
`tmp/metacompare.csv`.

Before carrying a blocker forward, write down the one command that would settle
it. If that command can be written, the item is not blocked -- it is queued.

### 8h. Where the tools live

    tools/fullstack_docs/docpush_preflight.py     THE preflight -- five checks
    tools/coordination/help_build_order_check.py  step 4: ordering + binding
    tools/coordination/help_store_check.py        step 5: the join + set diff
    tools/coordination/cmd_source_index.py        command -> handler -> source file

None of them need the engine, a build, or a network. All run read-only.

### 8i. I built the second spelling. Read this before adding a tool.

Sections 8 through 8h were first written around a NEW second copy of
`docpush_preflight.py`, under `tools/coordination/`. **One already existed** --
`tools/fullstack_docs/docpush_preflight.py`, tracked since 2026-08-05, owner
member.derald, lane AIF-088. Same filename. Same stated purpose. The duplicate
was removed in the same commit that folded its checks in, so the coordination
path deliberately no longer exists and is named here as history, not as a
citation. I committed the
duplicate in `48ba947e6` on the same day I fixed an R5 defect in
`helpdata_export_dbf.cpp` and wrote 8e recommending a prior-art check -- which I
then never ran on my own tool's name.

The content was complementary and nothing was lost: the old one checks CONTENT,
the new checks were ORDER, and they are now steps 4 and 5 of the one preflight.
The new file is renamed `help_build_order_check.py`, for what it checks.

**The rule, and it is the same rule as AIF-126:** before adding a tool, a gate,
a script or a checker, search for the name AND the purpose. `git ls-files |
findstr <word>` costs one second. Two files with one name is not a naming
problem -- it is two answers to one question, and one of them will be wrong
later. The prior-art check exists; run it on what you are about to build, not
only on what you are about to claim.

## 9. Never count a raw authority

Added 2026-08-25 after three counts went wrong in one session, all the same way:
a number taken from an authority that holds more than one KIND of thing.

    COMMANDS.dbf    320 distinct names = 288 commands + 32 FUNCTION entries
                    reached through the function command-line bridge. A name
                    also present in SYSFUNC is a function, not a command.
    SYSFUNC          75 rows, and HELP FUNCTIONS prints 73. STRCAT and TRIM are
                    ALIAS names (->CONCAT, ->RTRIM) carried in a FunctionDoc
                    alias field in function_catalog.cpp -- WHICH IS IN NO TABLE.
                    SRC_AUTH does NOT tell you this: it splits 68/7 and five of
                    its seven builtin_registry rows are ordinary printed
                    functions. Harvest provenance, not alias status.
    @dottalk.usage  231 files is the CONTRACT estate. @dottalk.file is 578 and
                    is a provenance header, not a contract.
    HELP_TOPIC      665 rows across NINE catalogs -- DOT 300, FOX 170,
                    SYSTEM 138, ED 29, EDU 15, UI 6, INTERNAL 4, EXT 2, DEV 1.
                    A four- or five-catalog list is wrong and omits the third
                    largest.

**Do not re-derive these. Run `python tools/fullstack_docs/stack_audit_v1.py`
and read check G (COUNT_KINDS) in the report's Detail section**, or take
identities from `build_reference_authority_crosswalk.py`, which assigns
`entity_type` (COMMAND / FUNCTION / ARGUMENT) and has since 2026-07.

**The numbers above are already stale by design.** They are here to show the
SHAPE of the mistake. G re-measures; this section does not.

**Two of the four bullets above were wrong when first written**, in a document
whose subject is not getting these wrong, and the check caught both on its first
run. That is the argument for running it rather than reading this.
