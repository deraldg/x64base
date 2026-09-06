# Primary key policy -- assembly and implementation plan

Lane: **AIF-156**, primary-key policy. Claimed 2026-09-06, run
`COWORK-20260906-001`, `member.ai.claude.cowork`. Status: **review-needed**.
The author does not self-approve.

## The finding, measured rather than argued

x64base has a real primary-key facility and enforces it nowhere.

Measured 2026-09-06 on build `Sep 05 2026 21:18:51` (`d16639c7` dirty) with
`tmp/pkprobe/pk_enforcement_probe.dts`:

| probe | result |
|---|---|
| `SET UNIQUE FIELD SID PRIMARY` | accepted; `SET UNIQUE` reports `SID (PRIMARY)` |
| APPEND x3 into a blank key | auto-bumped 1, 2, 3 |
| native `REPLACE SID WITH "1"` over a row holding 3 | **ACCEPTED** |
| close, reopen, re-read | duplicate persisted |
| `VALIDATE UNIQUE FIELD SID` | found it: `dup value='1' at rec 3 (first seen at rec 1)` |
| declaration after close/reopen | survived (registry buckets by TABLE NAME) |
| `SQLSEL INSERT` of a duplicate | **ACCEPTED**, committed through table buffer + WAL |

Final table: SID 1, 1, 1, 2.

### What is designed, and is worth keeping

- Declaration per table: `SET UNIQUE FIELD <f> ON|PRIMARY`, bucketed by table
  identity (`unique_registry.cpp`, Phase 2 / AIF-074 P1.1).
- Generation on APPEND into a **blank** key field, inside
  `try_lock_table` / `unlock_table` -- so `max+1` is taken by one writer at a
  time, the same discipline `bbs_store::next_id` uses.
- **A deleted row's key is reserved until PACK**, because the scan walks
  deleted physical records on purpose. A deleted row can be RECALLed.
- `VALIDATE UNIQUE FIELD <f> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]`.
- A workspace posture carries the declaration through `KEY <table> <field>`
  lines (`cmd_workspace.cpp`), so it is not purely session-local.

### What is unfinished, and why "by design" was the wrong reading

This session first described the behaviour as generate-and-remediate **by
design**. That was charitable to the code rather than a reading of it. Four
things say unfinished:

1. `field_constraints.hpp` names its call sites -- *"REPLACE, REPLACE_MULTI
   Pass 1, APPEND finalization"* -- and is wired to **none of them**. Its only
   caller in the tree is `sqlsel_statement.cpp`.
2. The same header says *"UNIQUE / PRIMARY enforcement remains index-backed"*,
   describing enforcement that exists in no file. A promissory note in the
   present tense. `CDX ADDTAG` has no UNIQUE keyword and no index writer
   carries a unique flag.
3. `unique_registry.cpp`: *"storage/backfill policy belongs elsewhere"* -- a
   question deferred and never picked up. The registry is a process-local
   `static unordered_map`, so a declaration dies with the shell.
4. **`VALIDATE UNIQUE ... REPAIR` renumbers duplicate keys.** For a PRIMARY
   key that is a hazard, not a remedy: if another row references the key,
   renumbering it breaks the reference silently. A finished policy refuses the
   write; renumbering is what you do to data you inherited.

## The plan, in dependency order

### Step 0 -- the spec (this deliverable)

`pk_policy_regression.dts`, 10 graded markers, derived not declared:
4 guards `PKP_G1..G4`, 6 arms `PKP_T1..T6`, contiguous.

Written in two halves and graded differently:

- **Part A (PKP_G1..G4, T1..T3) -- GREEN TODAY.** Declaration, generation, the
  deleted-key reservation, the recall that proves the reservation mattered,
  and VALIDATE finding a duplicate in data that arrived dirty. These lock in
  what already works. **If Part A ever reds, the policy work broke something
  that was fine.**
- **Part B (PKP_T4..T6) -- RED TODAY, BY DESIGN.** Native REPLACE, SQLsel
  INSERT and SQLsel UPDATE must each refuse a duplicate. INSERT and UPDATE are
  asserted separately because they reach the buffer by different paths and a
  fix wired into one is not evidence about the other.

**Do not weaken Part B to make the suite green.** A green Part B on a build
with no enforcement means the arm stopped discriminating.

NOT CLAIMED by this spec, stated rather than implied: persistence across a
restart (a `.dts` runs in one process; needs a two-run harness), concurrency
(one writer), and referential integrity (out of scope).

Registry placement, when the validator exists:

- Bump `constexpr std::array<RegressionSpec, 77>` at `cmd_regression.cpp:196`
  to **78**. The size is hand-maintained; adding an entry without bumping it
  is a hard compile error, which is the intended behaviour.
- Add `PkPolicyV1` to `enum class RegressionValidator` after `DefFamilyV1`.
- Entry is `false` for `in_default_suite` -- **explicit-run while Part B is
  red.** A partially-red spec must not enter `REGRESSION ALL`.
- Promote to the default suite only when Part B is green and soaked, following
  the NULLASSERT precedent: two green runs on a build nobody changed anything
  on, then the flag moves, then a rebuild, then read `REGRESSION LIST` for the
  `[default]` tag BEFORE believing the run.

### Step 1 -- persistence (do this first; no write paths change)

A key that evaporates on restart is a session hint, not a constraint.

The house pattern already exists and is the obvious fit: `WORKSPACES` is an
ordinary x64 table -- the map drawn in the same ink as the territory. A key
declaration belongs in a catalog table read at USE time, or in the DBF header.

**OPEN DECISION, OWNER'S TO MAKE, AND IT IS A SCHEMA COMMITMENT:** catalog
table or header?

- *Catalog table* -- queryable, attributed, versionable by the same supersede
  chain the workspace catalog uses; costs a read at open; a table can be
  missing.
- *Header* -- travels with the file, cannot be separated from the data it
  describes; costs a format change and a compatibility question for every
  reader, including the VFP-flavour and x32 paths.

Step 1 makes `PKP_T4..T6` no less red. It is sequenced first because it is the
only step that changes nothing about writes, and because the answer determines
what step 2 reads.

### Step 2 -- one choke point (engine; needs an explicit go for `src/xbase`)

Enforcement scattered across `cmd_replace`, `cmd_replace_multi`, append and
sqlsel will drift apart. The present state is the proof: three declared call
sites, one wired.

It belongs where writes converge -- around `replaceFieldStored` /
`writeCurrent` -- so every path inherits it rather than each remembering.

Risk, stated plainly: this is the step where a mistake corrupts data rather
than annoying a user. It wants its own proof before it lands, not after.

### Step 3 -- refuse, do not renumber

`VALIDATE UNIQUE ... REPAIR` survives as a tool for inherited data. It stops
being the mechanism. Its usage text should say which of the two it is.

### Step 4 -- the two documentation defects this uncovered

- **`SET UNIQUE FIELD <name> PRIMARY` ships with no usage line.** The command's
  own voluntary block documents `ON|OFF` only, so `SET UNIQUE USAGE` will not
  tell anyone the keyword exists. Same shape as the usage contract that lost
  three keywords.
- **The site's comparison row.** `content/products/... ecosystem-feature-
  comparison.mdx` says "no enforced primary key". That is LITERALLY TRUE and
  wrong by omission -- it implies no facility exists. Proposed replacement is
  in the session notes; it should not ship until step 0 is committed, so the
  page cites a spec rather than a conversation.

## Why the capability sweep could not see this

The freshness gate added on 2026-09-06 builds its authority from
`kRegressionSpecs`. There is no spec for primary keys, so there is no
capability, so no page could contradict one. **A gate generated from the
regression registry can only see what has a spec.** That is a real limit of
that mechanism and this lane is its first demonstration -- which is an argument
for step 0 independent of everything else.
