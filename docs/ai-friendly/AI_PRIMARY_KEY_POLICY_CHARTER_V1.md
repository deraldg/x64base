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

**RULED 2026-09-06 BY THE OWNER: A CATALOG TABLE.** R-number pending claim.

The alternative was a DBF header descriptor, and it was not dismissed -- it is
the philosophically stronger answer, because a primary key is a property of the
data and a header carries it wherever the file goes. What decided it was
REVERSIBILITY and RISK SURFACE:

- The house already has the machinery. `WORKSPACES` is an ordinary x64 table
  with a supersede chain, attribution and history; a key catalog is the same
  shape and needs no new concepts.
- A header change touches EVERY reader -- x64, x32, the VFP-flavour path, both
  x64 DBF readers (one of which this tree has already recorded as silently
  wrong), and Visual FoxPro itself, which must still open the file. That risk
  is measured rather than hypothetical: the `_NullFlags` bit-order work in the
  same header cost two commits in this tree because the order was got wrong.
- A catalog can later be superseded by a header. A shipped header format is
  very hard to walk back.

**THE COST OF THE RULING, STATED SO IT IS NOT FOUND BY SURPRISE:** the
constraint is NOT carried by the file. Copy a `.dbf` out of the tree and its
primary key does not go with it. For a primary key that is a real semantic
loss, not a technicality, and it is the strongest argument the header option
had. Anyone revisiting this should revisit it on those grounds and not on
convenience.

Step 1 makes `PKP_T4..T6` no less red. It is sequenced first because it is the
only step that changes nothing about writes, and because the answer determines
what step 2 reads.

**CONCRETE SHAPE, NOW THAT IT IS RULED.** A key catalog table holding at least
`(table identity, field name, kind)` where kind distinguishes UNIQUE from
PRIMARY; written by `SET UNIQUE FIELD <f> ON|PRIMARY`; read at `USE` and cached
onto the area so step 2's choke point does not pay a catalog read per write.
Two questions this raises that the ruling does not answer and that should be
settled before code rather than during it: what invalidates the cached copy,
and whether a table opened with no catalog row present is an error or simply a
table with no declared key. The second is the one that decides whether existing
tables keep working.

**THE PARTIAL CARRIER THAT ALREADY EXISTS.** A workspace posture writes
`KEY <table> <field>` lines and replays them into `set_unique_field` /
`set_primary_field` on LOAD (`cmd_workspace.cpp`). That is a second declaration
of where a key lives, and once the catalog exists it becomes a THIRD ROUTE to
the same state. It should be reconciled rather than left to drift -- the
`field_constraints.hpp` lesson in this same lane is what four live declarations
of one concept costs.

### Step 2 -- one choke point (engine; needs an explicit go for `src/xbase`)

Enforcement scattered across `cmd_replace`, `cmd_replace_multi`, append and
sqlsel will drift apart. The present state is the proof: three declared call
sites, one wired.

It belongs where writes converge -- around `replaceFieldStored` /
`writeCurrent` -- so every path inherits it rather than each remembering.

Risk, stated plainly: this is the step where a mistake corrupts data rather
than annoying a user. It wants its own proof before it lands, not after.

#### Step 2 dependency: the write path cannot name a field's obligations

Measured 2026-09-06 while asking a different question -- how does the table
layer know a field is indexed, so it can mark the index stale. It does not.

`mark_stale_field(area0, field1)` at `table_write.hpp:94` fires
UNCONDITIONALLY on every buffered field write, next to `set_dirty` and with no
index question anywhere near it. So `stale_bits` records FIELDS WRITTEN, not
INDEX FIELDS THAT WENT STALE, and from the automatic path `dirty` and `stale`
now carry identical information. The one consumer, `stale_fields_string_for_
area()` in `table_buffer.cpp:166`, turns the bitmap into names for a display
string capped at 120 characters. Every other reference is a `clear_`. The
`TABLE BUFFER STALE|FRESH|STALEALL|FRESHALL` verbs set the flag BY HAND.

THE DISTINCTION IS VESTIGIAL AND THE STRUCTURE PROVES IT. `AreaState` carries
BOTH `bool stale_any` and `std::uint64_t stale_bits[kWords]`, and `is_stale()`
returns the OR of them. A per-field bitmap only earns its place if something
once asked a question about each field individually; `stale_any` alone serves
every surviving use. The owner's recollection is that the original design
marked an indexed field DIRTY AND STALE and a plain field DIRTY ONLY. The
shape of that design is still standing with its predicate removed.

CAUSE NOT ESTABLISHED, stated rather than guessed. The pickaxe over
`mark_stale_field` finds exactly one commit: `fecc3951e`, 2026-07-14,
"Checkpoint runtime source and separate engine profiles" -- which reads as a
bulk import, and a bulk import flattens what came before it. The CNX
transactional work (XIDX-TXN-02) is 2026-07-31, two weeks LATER, so the
batch-to-transactional hypothesis is NOT supported by this repository's
history. The history that would settle it may not be here.

AND THE CONTAINER CANNOT ANSWER IT EITHER, which is the part that makes this a
step 2 dependency rather than a separate cleanup. The x64 CDX is an LMDB
environment with ONE NAMED LMDB DATABASE PER TAG -- `std::unordered_map<
std::string, MDB_dbi> dbis_`, keyed by tag name. That name is the ENTIRE
per-tag metadata: no key expression, no field index, no descriptor. Nothing in
the tree parses a FoxPro compound-index tag header.

So "which field does this tag index" is answered by MATCHING THE TAG NAME
AGAINST THE FIELD NAME, in two duplicate implementations that do not agree:
`field_index_for_tag_()` at `cdx_native_backend.cpp:72` trims and handles an
embedded NUL; `IndexManager::activeTagFieldIndex1()` at `index_manager.cpp:382`
does neither. Consequences:

- `CDX ADDTAG SID` works BY CONVENTION, not by knowledge. A tag named `BYNAME`
  over field `LNAME` resolves to 0 -- "no field" -- and any caller asking
  whether that field carries a tag gets a confidently wrong answer.
- AN EXPRESSION TAG CAN NEVER RESOLVE. `UPPER(LNAME)` matches no field name,
  ever. This is the same blocker recorded in `compute_next_numeric()` against
  an index-backed autokey fast path, now confirmed STRUCTURAL rather than a
  hedge.
- It is the FIFTH live declaration of what a field name is, joining the
  ADDTAG/REPLACE pair (unified via `xfg::resolve_field_index_std`) and
  BUILDLMDB's raw `textio::ieq` and REBUILD's `normalize_field_name`, both
  recorded against MWXSHAKE.

#### The CDX sidecar already exists, and it changes the cost of this

**A `.cdx.meta` SIDECAR SHIPS TODAY.** Measured 2026-09-06: plain `KEY=VALUE`
text, 130-166 bytes, written and read by `src/xindex/cdx_meta.cpp`. It is
ALREADY VERSIONED:

    META_VERSION=1
    BACKEND=lmdb
    KIND=v64
    VERSION=100
    RECLEN=47
    FIELDS=2
    HASH=415,126,891,304,751,935
    SOURCE=dbf\x64\BUILDING.DBF

It describes THE TABLE THE CONTAINER WAS BUILT FROM -- record length, field
count, a fingerprint, the source path. NOT ONE WORD ABOUT TAGS.

THIS MAKES THE FIX MUCH CHEAPER THAN A CONTAINER FORMAT CHANGE. A `TAG=<name>,
<field_index1>` line per tag needs no change to the `.cdx` itself, raises no
VFP compatibility question, and `META_VERSION` is already there to gate it: an
old reader skips a line it does not know, a new reader gets the answer without
name-matching. The earlier draft of this section assumed a container format
change was required; it is not.

**THE SIDECAR IS NOT RELIABLY PAIRED, AND ANYTHING READING IT MUST SAY SO.**
Measured on the x64 index root: `CLASSES.cdx`, `COURSES.cdx`, `DEPT.cdx`,
`MAJORS.cdx`, `ROOMS.cdx`, `STUD_MAJ.cdx` and `table.cdx` have NO meta;
`IDXBENCH.cdx.meta`, `IDXFAIL.cdx.meta`, `PHYSICAL.cdx.meta` and
`VUREP.cdx.meta` are ORPHANS with no container. So absence must mean UNKNOWN,
never "this table has no tags" -- the same shape as the missing-catalog-row
question step 1 is already holding. There is also case duplication
(`CLASSES.cdx` beside `classes.cdx.meta`, and five more), which on a
case-insensitive filesystem is one stem reached two ways: a sixth spelling of
identity sitting next to the five spellings of what a field name is.

**CNX HAS NO SIDECAR AT ALL.** `.cnx` files exist under `INDEXES/vfp/` and
`INDEXES/sandbox/` with nothing beside them, and `cmd_erase.cpp` builds a
`.cdx.meta` path and no `.cnx.meta`. A sidecar-based answer therefore covers
CDX and leaves CNX exactly where it is, which matters because
`container_supports_tag()` treats the two identically.

**NO EVIDENCE THE SIDECAR EVER CARRIED PRIMARY / STALE / DIRTY.** The owner's
recollection is that it did. It was checked both ways and this tree does not
support it: all 86 `.cdx.meta` files on disk carry EXACTLY the eight keys
above, none more and none fewer; and `cdx_meta.cpp` knows exactly those eight
literals, with no orphan parsing for a key it no longer writes -- which is
usually where a removed feature leaves its fingerprint. As with the
`mark_stale_field` history, the evidence may simply live where the subapp did
rather than in this repository. RECORDED AS UNSUPPORTED RATHER THAN DISPROVED:
absence of a trace in one tree is not proof about another.

**THE SIDECAR IS NOT YET FIT TO CARRY A LOAD-BEARING CLAIM, AND THAT IS A
PREREQUISITE RATHER THAN A CAVEAT.** Measured 2026-09-06 and written up
separately because it is index-metadata durability rather than primary keys:
`.cdx.meta` is GITIGNORED (0 tracked, 86 on disk), so a fresh clone has none
and `index_manager.cpp:205` MINTS ONE FROM THE TABLE'S CURRENT IDENTITY on
first open. The fingerprint guard is hardened and correct, and it cannot be
older than the sidecar -- so after a clone every container is trusted exactly
once, unconditionally. Pairing is broken in both directions in four of ten
index roots, and `SOURCE` is unvalidated (49 absolute, 37 relative, 14 that
resolve to nothing, one empty) because `cdxmeta::matches()` never reads it.

Putting `TAG=<name>,<field_index1>` into that file today would mount the
primary-key answer on the same foundation. The sidecar repair is sequenced
BEFORE step 2 can use it.

**OPEN DECISION, OWNER'S.** Restoring the dirty/stale distinction on top of
name-matching would produce a flag that is right for conventionally-named tags
and quietly wrong for every other kind -- WORSE than today's
over-broad-but-safe behaviour, because it would look precise. The real options
are: put `TAG=<name>,<field_index1>` in the existing `.cdx.meta` (cheapest, no
format change, leaves CNX unanswered); put the field index in the container
itself, for which the precedent is already in this tree in a sibling format --
`TagDesc` in `local_index_stub.hpp` carries `uint32_t field_index1`, and the
x64 CDX design dropped it; or parse a real VFP key expression, which is a NEW
CAPABILITY rather than a restoration, since no code reads that header today.

Whichever is chosen, step 2's choke point needs to answer THREE questions
about a field and can name NONE of them today: is it indexed, is it unique, is
it the primary key. They are one predicate short each, at the same seam.

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
