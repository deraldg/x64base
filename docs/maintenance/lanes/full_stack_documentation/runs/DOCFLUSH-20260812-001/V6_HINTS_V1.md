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
`WORKSPACE CATALOG` (2026-08-12), which reports the two axes the catalog already
stored and never surfaced -- FMT (posture vs table bytes) and carrier (memo vs
file, read from the WSID prefix), plus size, areas, author and which rows are
superseded.

General rule for v6: **when a version number is proposed, check whether the
distinction is a payload difference or a placement difference.** Only the first
belongs in a format namespace.

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
