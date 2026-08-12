# Cowork session handoff -- 2026-08-12 (afternoon)

    session : member.ai.claude.cowork
    lanes   : AIF-070 (coworker, writeback arm), plus house-keeping
    commits : 5a4f9b3ec (path split + writeback arms), aa32edbc5 (REGRESSION FIND)
    status  : em-dash sweep staged but UNCOMMITTED; scanner work PAUSED for review

---

## Good-neighbor notes

Filed per `GOOD_NEIGHBOR_POLICY_V1.md` section 3. The quip rung was checked and
does not apply: `session_coordinator.py status` reports **no live sessions**,
only three stale entries older than 240 minutes. So these land durably here.

### 1. To whoever holds the uncommitted work in the coordination + staging tools

**Lane:** AIF-050 (claim held by `member.ai.claude.cowork`, run
AIPR-20260722-007) and the identity smoke tests.

**What I touched, and then put back.** This session swept em-dashes out of
source and scripts (215 replacements across 141 files, comments only). Four of
the files it swept turned out to carry YOUR uncommitted working-tree changes,
so my cosmetic edit would have fused with your in-progress work in the shared
tree. **I reverted my change in all four rather than commit over you:**

| file | em-dashes I reverted | now |
|---|---|---|
| `tools/staging/prepush_gate.py` | 14 | left as you have it |
| `tools/coordination/session_coordinator.py` | 2 | left as you have it |
| `tools/coordination/aif_collision_gate.py` | 1 | left as you have it |
| `tests/identity/identity_entities_smoke.cpp` | 2 | left as you have it |

Verified after reverting: those four carry **zero** em-dash swaps in their
diffs, and none of them appear in this session's staging pathspec
(`dottalkpp/data/tmp/EMDASH_SWEEP_FILES.txt`, 141 paths, checked).

**Consequence:** 19 em-dashes remain in those four files. Nothing is broken --
they were there before today.

**Action you need:** none urgent. When your work lands, sweep those 19 (or say
the word and a later session will). They are the only known gap in an otherwise
complete source-side sweep.

**Why I did not just fix them:** concurrent sessions share ONE working tree,
and a tidy-up is not a reason to touch someone's live edit. This session
already breached that boundary once today, regenerating Codex's preserved
`ai_runs.yaml`, which is exactly why the entanglement check was run at all.

### 2. To the owner of `check_house_style.py` (AIF-082)

**This one is worth your attention more than the sweep is.**

`CLAUDE.md` states the rule as "no em-dashes in **scripts or docs**". The gate
implements `CHECKED_SUFFIXES = (".md",)` and inspects ADDED lines only. So the
rule covers scripts and the enforcement does not, and nothing announces the
difference.

**Measured receipt, from this session's own commit:** `5a4f9b3ec` shipped
`src/cli/cmd_erase.cpp` with an em-dash in its line-11 banner comment, and that
commit's gate printed `house-style: PASS`. The gate is not wrong -- its message
says "no non-ASCII in added DOCUMENTATION lines", which is precisely what it
checks. The rule is simply wider than its enforcement. That gap is how 350
em-dashes accumulated across `.cpp` / `.hpp` / `.py` / `.dts` / `.ps1` with
every commit green.

**Action, if you want it:** extend the checked suffixes to source and scripts.
**Do NOT extend it to blanket non-ASCII.** Measured in this tree: 5390
box-drawing characters carry report and TUI rendering, and 312 accented
characters serve the es/fr/de/it localized surfaces that `REGRESSION LANGUAGE`
proves. A blanket rule destroys both. The enforceable set is TYPOGRAPHIC:
em-dash, arrow, bullet, section sign.

I did not make this change. It is your tool, the fix has a real false-positive
hazard, and it deserves your call rather than mine.

### 3. To `member.ai.grok.xai` (AIF-070)

Continuing the coworker note from `5a4f9b3ec`. Two further things landed in
your lane's neighbourhood today, both already committed and both recorded in
that commit's message: the CWD-vs-DATA path split closed across
`WORKSPACE WRITEBACK TO`, `ERASE DIR` and `FILE()`, and the retraction of a
false-green Linux proof that this session had filed as evidence that morning.
The claim on AIF-070 is unchanged.

---

## What is PAUSED and why

`WORKSPACE OPEN`'s directory scanner. Two findings, one surface, **nothing
built**:

- backups (`.__wbak`, `.__fldbak`) are admitted as tables -- 26 areas for a
  13-table posture, each backup bound to the LIVE table's `.cdx`;
- `WORKSPACE OPEN <dir>` resolves CWD-relative and opens nothing SILENTLY.

Owner paused this for an Active Peer Review. Packet written and self-contained
for a one-way reviewer:
`PEER_REVIEW_WORKSPACE_SCANNER_AND_WBAK_PLACEMENT_V1.md`. It carries the
measured retention facts (`.__wbak` is depth-one, kept forever, previous
generation silently discarded), the owner's house-TMP option worked through
with its trade-off, and five explicit decisions.

`workspace_wbak_scan.dts` is written and green (4/4) but UNREGISTERED, pending
the same ruling.

## Known broken, introduced by this session

`5a4f9b3ec` made `fn_string.cpp` depend on `paths::get_slot` /
`resolve_in_slot`. `dt_meta` compiles `fn_string.cpp` but links neither
resolver, so **the `metacollect` target no longer builds**.
`DOTTALK_BUILD_METACOLLECT` defaults OFF, which is why every build and every
gate passed while the target was unbuildable.

Fix verified in a scratch tree (add `src/common/path_resolver.cpp` and
`src/common/path_state.cpp` to `dt_meta`; links and builds clean). NOT applied,
because `dt_meta` carries a stated safety boundary -- "no HELP DATA rebuild, no
CMDHELPCHK mutation, no DBF writes" -- and `path_state` brings process-wide
mutable path-slot state into a library built to be minimal. That is an owner
call, not a steward call.

**Consequence:** `SYSFUNC_IMPORT_v1.csv` cannot be regenerated until this is
fixed, so the `FN_COVERAGE` warn on `FILE` (75 implemented vs 74 in SYSFUNC)
stays open.

## Still owed, unstarted

- `WORKSPACE OPEN <dir>` resolution (paused for review).
- DTSCHEMA v3 regression (owner-identified, never written).
- `RECNO` as a predicate identifier evaluates empty and returns a confident
  zero -- `SMARTLIST ... FOR RECNO > 195` gives 0 records with no error, while
  the same query on a field predicate works and `RECNO` renders fine as a
  projection column.
- Whether the path split gets its own AIF number. It is not AIF-070's.
