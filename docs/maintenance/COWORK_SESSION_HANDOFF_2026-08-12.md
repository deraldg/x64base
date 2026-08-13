# Cowork session handoff -- 2026-08-12 (afternoon)

    session : member.ai.claude.cowork
    lanes   : AIF-070 (coworker, writeback arm), full_stack_documentation (v5),
              plus house-keeping
    status  : 8 commits landed. Scanner work PAUSED for Active Peer Review.
              Flush v5 OPEN at Gate 0, blocked on the metacollect repair below.

    UPDATED at end of session. The first version of this file was written after
    commit 2 of 8 and its "still owed" list went stale within the hour -- which
    is itself the argument for updating a handoff rather than leaving the reader
    to reconcile it against the log.

    commits, in order:
      5a4f9b3ec  CWD-vs-DATA path split closed across WRITEBACK TO / ERASE DIR /
                 FILE(); writeback's three untested arms proven; a false-green
                 Linux proof RETRACTED across closeout, registry and log
      aa32edbc5  REGRESSION FIND -- the question-to-spec bridge
      4c584ba8f  em-dash sweep (215 replacements, 141 files) + this handoff +
                 the peer-review packet
      6f7e73e14  WORKSPACE LOAD refuses a shortfall BEFORE it closes anything
      28a14d653  load-shortfall fixup: a destroyed fixture and a shadowed name
      c04ac1bdb  contracts corrected; dotref.hpp brought up to the verb surface
      42e0ecc56  flush v5 opened (DOCFLUSH-20260812-001) + v6 hints
      a350c00ef  CMDHELP's preview now states its own scope

---

## Read this first if you are picking up the lane

- **Flush v5 is OPEN at Gate 0**, not closed:
  `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260812-001/`.
  Gate 0 envelope, Gate 2 baseline (+ its 103 KB transcript), and
  `V6_HINTS_V1.md` are committed. **Gate 0 does not pass until metacollect is
  repaired** -- see "Known broken" below.
- **`V6_HINTS_V1.md` is the highest-value file in that directory.** It carries
  the LEGACY-first rebuild sequence as a seven-step gate, the finding that HELP
  DATA carries NO provenance at all, the three-separately-authored-descriptions
  problem, the five expression functions publishing as unsupported commands, and
  a "settled -- do not re-derive" section.
- **`WORKSPACE LOAD` behaviour CHANGED.** A shortfall now aborts before anything
  closes. Anything relying on a silent partial restore needs the new `PARTIAL`
  keyword. Proven by `WORKSPACE_LOADSHORT` (6/6, every arm mutation-killed).

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

**Waiting on an owner ruling (nothing else can proceed on these):**

- **The `dt_meta` safety boundary** -- unblocks metacollect, SYSFUNC, the
  FN_COVERAGE warn, and flush v5's Gate 0. Highest leverage item here.
- **`.__wbak` placement** -- filter the scanner, relocate the backups, or route
  them to the house TMP slot. With the Active Peer Review; packet is
  `PEER_REVIEW_WORKSPACE_SCANNER_AND_WBAK_PLACEMENT_V1.md`.
- **`WORKSPACE OPEN <dir>`** resolves CWD-relative and opens nothing SILENTLY.
  Same review, same surface, deliberately not fixed separately so one ruling
  covers the whole scanner.
- **Whether `workspace_wbak_scan.dts` becomes a registered regression.** Written
  and green (4/4), unregistered by choice.
- **Whether the path split gets its own AIF number.** It is not AIF-070's -- it
  predates that lane and any verb taking a relative target was exposed.
- **The five expression functions publishing as unsupported DOT commands**
  (FILE, UDATE, UDATETIME, UNOW, UTIME). Recorded in the v6 hints with three
  candidate rulings.

**Owed work, no ruling needed:**

- `SYSFUNC_IMPORT_v1.csv` regeneration -- blocked on metacollect, not on a
  decision.
- `RECNO` as a PREDICATE identifier evaluates empty and returns a confident
  zero: `SMARTLIST ... FOR RECNO > 195` gives 0 records with no error, while the
  same query on a field predicate works and `RECNO` renders fine as a PROJECTION
  column. Measured; unfiled.
- 19 em-dashes in the four files reverted for good-neighbour reasons (section 1).
- dotref summary length: this session's three entries added 96 rows, about 32
  each, against roughly 3.5 rows per entry across the other ~255. A trim to
  syntax-plus-essentials was offered and not yet ruled on.

**CORRECTED -- do not chase this one:**

- The DTSCHEMA v3 regression is **not** missing. `WORKSPACE_V3` /
  `workspace_v3_selflocate.dts` exists, is registered, and runs green. It is
  THIN (one marker for a feature making six separable promises), which is a
  coverage question rather than an absence. The earlier entry here said "never
  written" because this session did not check prior art before believing it --
  the same failure recorded in section 7 of the v6 hints.
