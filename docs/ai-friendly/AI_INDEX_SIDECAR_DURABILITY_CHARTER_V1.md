# Index sidecar durability -- assembly and implementation plan

Lane: **AIF-157**, index-sidecar-durability. Claimed 2026-09-06, run
`COWORK-20260906-001`, `member.ai.claude.cowork`. Status: **review-needed**.
The author does not self-approve.

Blocks **AIF-156** step 2 (`docs/ai-friendly/AI_PRIMARY_KEY_POLICY_CHARTER_V1.md`),
which would otherwise build a write-time choke point on a tag identity this lane
exists to repair.

No engine code is changed by this document. Everything below is measured or
proposed; nothing here has been implemented.

## The finding, in two halves

An index makes two promises, and the tree keeps them in two very different ways.

| promise | question it answers | where it lives | consulted at open |
|---|---|---|---|
| **identity** | is this index built for THIS TABLE's schema? | `.cdx.meta` sidecar, 8 keys | yes -- but the sidecar is untracked |
| **currency** | is this index current with the table's DATA? | three header flags and a per-tag timestamp, all durable | **CDX: no. CNX: torn-save only.** |

Identity **cannot** answer the currency question, and this is the hinge of the
whole lane: changing a field's VALUE touches no schema byte, so `RECLEN`,
`FIELDS` and `HASH` stay identical across any amount of data drift. A fingerprint
that matches proves the index was built for this table. It proves nothing about
whether it still describes it.

## Half one -- a hardened guard mounted on a disposable file

`src/xindex/cdx_meta.cpp` writes and reads a plain KEY=VALUE sidecar with eight
keys: `META_VERSION`, `BACKEND`, `KIND`, `VERSION`, `RECLEN`, `FIELDS`, `HASH`,
`SOURCE`. `HASH` is an FNV-1a over each field's name, type, length and decimals.
`openCdx` reads it and refuses on ANY mismatch.

Measured 2026-09-06:

| probe | result |
|---|---|
| `.cdx` containers tracked | 17 |
| `.cnx` containers tracked | 24 |
| `.cdx.meta` sidecars tracked | **0** |
| `.gitignore` rule | `:220` lets `.meta` through, `:350` takes it back |

So a clone arrives with a TRACKED container and NO fingerprint. The first open
mints one from whatever the table currently is. **The guard then validates the
table against itself and can never fail.**

`.gitignore:347` justifies the exclusion by calling sidecars "Regenerable" --
which is the exact property that defeats the guard -- and cites "(0 tracked)",
which is circular reasoning from a state the rule itself creates.

**DELETING `.gitignore:350` IS A RECOMMENDATION REQUIRING OWNER ACTION. It is
not a step in this plan and this session has not done it.**

### The ramfs exemption is correct and stays

`src/xindex/index_manager.cpp:114` returns before the sidecar for virtual
containers, routing them to the native CDX-V64 backend instead. That is not the
defect. The owner's reading -- "an index file was assigned a `.meta` only if it
needed one" -- is correct.

**CORRECTED 2026-09-06, and the correction matters because the original reason
was the weaker one.** This section first argued that a container living in RAM
dies with the process, so it has nothing to carry forward and nothing to
fingerprint. True, and a POLICY argument -- the kind that can be revisited by
someone who decides RAM containers should be fingerprinted after all.

The owner's ruling is a CAPABILITY BOUNDARY and it cannot be revisited that way:
**CDX automatically falls back to "cnx" mode in a vdisk, because LMDB indexes
cannot be used there.** There was never an LMDB-backed index inside a virtual
container for a sidecar to describe or a staleness flag to describe it. The
exemption is not a choice about what deserves a fingerprint; it is the absence
of the thing a fingerprint would be about.

This distinction is load-bearing for step 3. Under the lifetime argument a
RAM-VFS fixture is merely USELESS. Under the capability boundary it is
IMPOSSIBLE -- see that step.

## Half two -- currency has a durable home, and nothing reads it

**This section replaces a claim that was drafted, measured false, and is recorded
here rather than quietly dropped.** The first draft of this charter said currency
"has no durable home at all" and proposed three candidate homes to choose
between. That was wrong in the most expensive direction: **it would have built
what already exists.** Currency has THREE durable homes, all in the container
formats themselves. The defect is that they are not consulted.

| mechanism | declared | written | read |
|---|---|---|---|
| `CDX_HDRF_DIRTY` | `include/cdx/cdx.hpp:34` | **never -- `cdxfile::set_dirty` has ZERO callers** (defined `src/cdx/cdx_file.cpp:153`) | **nowhere in the tree** |
| `CNX_HDRF_DIRTY` | `include/cnx/cnx.hpp:26` | `src/cnx/cnx_file.cpp:275-276`, raised at `src/xindex/cnx_backend.cpp:870` | `src/xindex/cnx_backend.cpp:440` -- **torn-save only** |
| `SNX_HDRF_DIRTY` | `include/snx/snx.hpp:40` | n/a -- SNX has no implementation at all | n/a -- see the correction below |
| `TagDirEntry.updated_ts` | `include/cdx/cdx.hpp:62`, `include/cnx/cnx.hpp:54` | every rebuild: `src/xindex/cdx_native_backend.cpp:469`, `src/xindex/cnx_backend.cpp:608` | **never compared to anything** |

**CORRECTED 2026-09-06, RE-MEASURED. TWO CELLS OF THIS TABLE WERE WRONG, and
one of them was wrong in the direction that would have wasted the next session.**

`CDX_HDRF_DIRTY` was recorded as WRITE-ONLY -- "set and cleared", read by nobody.
It is not written either. `cdxfile::set_dirty` is declared at `include/cdx/cdx.hpp:114`,
defined at `src/cdx/cdx_file.cpp:153`, and **called from nowhere in the tree**;
`CDX_HDRF_DIRTY` itself appears at exactly three lines, all inside that
uncalled setter and its enum. The flag is therefore ALWAYS ZERO on every CDX
container ever written.

That changes step 2's dependency order, which is why it matters rather than
being a footnote. Step 2 item 1 said "give `CDX_HDRF_DIRTY` a reader". A reader
added today would read a permanently-zero flag: a currency check that checks
nothing while LOOKING like coverage -- strictly worse than no check, and the
exact false-green shape this lane exists to catch. **The writer comes first, or
with it. Never the reader alone.**

`SNX_HDRF_DIRTY` was recorded as "declared and never set", which invited step 2
item 4's "either wire it or delete the declaration". Both options are void.
There is no `src/snx/` directory, no CMake target names snx, and no `.cpp` in
the tree includes `snx/snx.hpp` -- only `snx_catalog.hpp` does. Every function
the header declares (`open`, `close`, `read_header`, `flush_header`,
`set_dirty`, `page_size`) is a declaration with no definition, and the header
carries no `inline`. It links today only because nothing calls it.

**AND THAT IS DELIBERATE, WHICH IS WHY THIS IS A CORRECTION AND NOT A FINDING.**
The header's own purpose block opens with "Future custom compound index family
(peer to CNX/CDX)". SNX is a format SPECIFICATION written ahead of its
implementation, not an implementation that lost its body. You cannot wire a flag
into a format with no body, and deleting one flag declaration from a file that
is entirely declarations is arbitrary. Item 4 dissolves.

The one residue worth an owner's eye is a single word: `include/snx/snx.hpp`
carries `status: supported` in its frontmatter while its purpose block says
"Future". That is machine-readable metadata disagreeing with the prose beside
it. `reserved` or `planned` would make the two agree; `supported` is a claim the
file does not keep.

`updated_ts` is the sharpest of the four. It is not a reserved field awaiting a
design -- it is **written on every rebuild, persisted in the tag directory, and
round-tripped on load and save** (`src/cdx/cdx_file.cpp:213-214` and `:231-232`).
Per-tag freshness is recorded on disk today. Nothing has ever asked it a
question.

`CNX_HDRF_DIRTY`'s read is real but narrow: `src/xindex/cnx_backend.cpp:440`
answers "was the container left mid-save", which is torn-write detection. A
container closed cleanly with a known-missing index entry is not mid-save, so
that read cannot see it.

### This was found once already, and half of it was fixed

`src/AIPortal/sessions/2026-07-30_cowork_house_index_vdisk/LANE_XIDX_TXN_02_M0_RECONCILIATION_V1_20260730.md`
section N5 -- *"the fail-safe backstop is declared but not wired"* -- recorded
that `wasStale()` had zero callers, that `CNX_HDRF_DIRTY` was never tested, and
that the per-tag fields were "available and unused". It called this "the most
actionable finding in the document."

Since then **`wasStale()` gained its consumer** -- that is precisely what
`IDXSTALE` exists to prove -- and **CNX gained its torn-save read**. The CDX half
was never wired, and it is the same half whose sidecar is untracked. **Both of
the `.cdx`'s durability mechanisms are inert, for two unrelated reasons.**

### What survives as a live defect

`src/xindex/index_manager.cpp`'s return-value contract is documented as
load-bearing: callers "treat false as an index-maintenance failure and mark
fields stale (see `src/cli/cmd_replace_multi.cpp`)", and the note above it names
the durable consequence in one sentence -- **"a missing entry stays missing until
REINDEX/REBUILD."**

So on a genuine maintenance failure against a tracked disk `.cdx`:

1. The missing index entry is a **durable fact on disk**.
2. The knowledge that it is missing is marked in `AreaState` -- **in memory**.
3. At exit, (2) is lost and (1) remains.
4. The next open cannot recover it, **because the durable flag that could carry
   it across is never read**.
5. The identity fingerprint matches perfectly, and the index answers.

**A transient maintenance failure becomes permanent silent staleness at the next
process boundary** -- not for want of a place to write it down, but for want of
anyone reading the place.

### Two corrections this session made to itself

Recorded rather than dropped, because a withdrawn claim that leaves no trace gets
re-derived by the next reader.

1. **"Currency has no durable home."** False. See the table above. The three
   flags and the per-tag timestamp all exist and all persist.
2. **"Native CDX-V64 serves a stale index across a restart behind a matching
   fingerprint."** False. `src/xindex/index_manager.cpp:114` routes native
   CDX-V64 to ramfs ONLY -- "Disk .cdx still routes to the LMDB CdxBackend
   below" -- and a ramfs container dies with the process, so the backend that
   cannot maintain is the one with nothing to persist. The symmetry was appealing
   and false; the routing is what settles it.

Same failure shape as the CRLF false alarm earlier in this run: a difference that
looked like a defect until the code that handles it was read.

## What is designed, and is worth keeping

- **The 2026-09-01 refusal hardening.** Until then a mismatch whose CORE SHAPE
  still matched -- same kind, version, reclen and field_count, differing only in
  `schema_hash` -- did not refuse. It OVERWROTE THE SIDECAR and opened. The cases
  it silently blessed are exactly a field rename, a same-width type change, a
  decimals change and a field reorder. The in-code note names reorder as the
  worst, "a tag re-pointed onto data at a different offset ANSWERS rather than
  refuses", and states the principle this whole lane rests on: **"A stale index
  that answers is worse than one that refuses, because nothing says the answer
  changed."**
- **The `IDXSTALE` / `CNXLIVE` split** in `src/cli/cmd_regression.cpp`. Two specs
  asserting opposite contracts for backends with opposite capabilities, kept
  separate so the XIDX-TXN-02 M1 inversion reads as a deliberate repointing
  rather than a silently retuned regression.
- **The CNX persistence deferral, which is a named milestone and not an
  oversight.** `src/xindex/cnx_backend.cpp` states it plainly: realtime "is a
  property of the in-memory payload; persisting it is a separate milestone", and
  "an edited disk CNX is correct for the session and reverts to its last rebuilt
  order afterwards." Per-edit writes were rejected on measured cost -- RUN1 is 4
  bytes per recno, so one tag block for a 1M-row table is about 4 MB. Design is
  in `docs/maintenance/XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md`.
  **Reverting to the last rebuilt order is a known-good state, not a hole.** It is
  not the defect above.

## What is unfinished

1. **The sidecar does not travel.** 0 of 41 containers ship one.
2. **`CDX_HDRF_DIRTY` is not written AT ALL** -- corrected 2026-09-06; it was
   recorded here as write-only, and `cdxfile::set_dirty` has zero callers, so
   the flag is always zero. `updated_ts` is written on every rebuild and never
   compared.
3. **No spec asserts either half.** Still true, and `IDXNAME` does not change
   it -- that spec proves TAG -> FIELD RESOLUTION and asserts nothing about the
   sidecar or about a durable dirty flag being read. Said explicitly because a
   new green spec in this lane is exactly the thing that could be mistaken for
   coverage it does not have. See below.
4. ~~**Tag -> field is answered by NAME MATCHING in two implementations that
   disagree.**~~ **RESOLVED 2026-09-06 (`403cb4072`).** It was FIVE, not two,
   and the fix was to route them onto `xfg::resolve_field_index_std` rather than
   collapse them into a sixth. See step 4. This also clears the second blocker
   on the `compute_next_numeric` index fast path in `src/cli/append_support.cpp`.

## Why no gate could see this

Eight index specs existed when this was written; `IDXNAME` (2026-09-06) makes
nine. `INDEX_X32` and `INDEX_X64` are default-suite; `INDEX_X64_CNX`,
`INDEX_TXN`, `IDXDIFF`, `VUREPAIR`, `IDXSTALE`, `CNXLIVE` and now `IDXNAME` are
explicit-run. **Not one asserts anything about the sidecar, and not one asserts
that a durable dirty flag is ever read** -- `IDXNAME` included, which is why
item 3 above is still open.

The only reference to `.cdx.meta` in the entire `.dts` corpus is a hand-cleanup
comment at `dottalkpp/data/scripts/mcc_add_notes_memo.dts:29-42`, warning a human
that deleting the `.cdx` leaves the sidecar behind and that `openCdx` trusts it.
**The corpus's single mention of the file is a warning that it outlives its
container and is believed anyway.**

The coverage is not merely absent. **It is structurally blind.**
`dottalkpp/data/scripts/index_maintenance_failure_proof.dts` (`IDXSTALE`), the
nearest instrument, builds its fixture entirely in the RAM VFS -- and ramfs is
the one routing that skips the sidecar by design. The closest spec runs on the
one lane where the sidecar is never created.

This is the AIF-079 shape again: a suite can be dense around a defect and blind
to it, and **density reads as coverage on every report we generate.** Three of
the four durability mechanisms in the table above are declared-but-unconsumed,
which is the same shape one layer down.

## Provenance -- the owner's account, measured

### On the history of batch mode

Owner, 2026-09-06: *"cnx used to reindex in batch mode because it could not
update the index key when the data mutated at runtime, now we can immediately
update the key so the batch mode is only used for rebuilds."*

**Confirmed in the code's own words**, `src/xindex/cnx_backend.cpp`: "XIDX-TXN-02
M1 -- realtime CNX maintenance. These were no-ops that set stale_ and returned
NORMALLY, so every CNX edit left the order wrong while reporting success. They
now maintain the loaded permutation." And on what batch became: "The table is the
ordering authority instead -- **exactly as it is for a rebuild**."

### On the loss of the art

Owner, 2026-09-06: *"the decay of the indexing meta data is likely because we
don't have a regression test that covers this indexing aspect, and also it was
solved and instituted before the ai portal and never got into a development lane
-- but that is not an excuse for losing established art."*

- `src/xindex/cdx_meta.cpp` has **two commits in its entire history**:
  `fecc3951e` (2026-07-14, "Checkpoint runtime source and separate engine
  profiles", a squashed import) and `3706da78c` (2026-07-25, a 1034-file mass
  backfill). **Neither authored it.**
- The AI portal lane opened at `62f35aa88` on 2026-07-12, **two days before the
  checkpoint**. The art did not slip past the portal; it arrived already built,
  with no authoring history for the portal to catch.
- `fecc3951e` is also the **only commit that ever touched `mark_stale_field`**.
- `fecc3951e` is also where the silent-refresh branch came from -- the trap
  removed on 2026-09-01, documented in-code as arriving "inside a bulk checkpoint
  commit (fecc3951e, 2026-07-14) with no design note and nothing in the tree ever
  explained it."

**One import delivered the sidecar, the only touch its staleness counterpart has
ever had, and a trap that took fourteen months to find.** "Never got into a
development lane" is not a mitigating circumstance here. It is the mechanism.

### The owner's stale/dirty hypothesis is RESOLVED, not merely unsupported

Recorded earlier as unsupported-not-disproved, on the evidence that 86 sidecar
files carry 8 keys and no vestigial parsing. **That search was looking in the
wrong file.**

The owner recalled that the subapp "knew which index fields were indexed and
marked them stale and dirty when changed, and regular keys just dirty." Every
element of that has a real referent:

- **stale** -- `stale_`, runtime, now consumed via the `wasStale()` transition.
- **dirty** -- `*_HDRF_DIRTY`, durable, in the container header.
- **knew which index fields** -- the per-tag directory, `updated_ts` and
  `stats_rec`, written per tag on every rebuild.

**The art was not lost. The storage for it was reserved, it is written, and
nothing reads it.** A mechanism that is never consulted decays exactly like one
that was deleted, and it is harder to notice, because every file listing and
every format document still shows it present.

## Owner ruling on shape (2026-09-06)

*"the sidecar meta should be a permanent fixture for a cnx and cdx ... meta
should travel and stay with the cnx containers ... whether a meta file is there
or not is a test we will make at runtime when we open an index anyway, no matter
our decision, so is it really more complex to make them conditional? I don't
think so."*

Recorded as the shape decision: **the sidecar is a permanent fixture, not
evidence and not a cache.** Conditional creation buys no simplicity, because the
existence test is paid on every open either way. The ramfs exemption is not a
counterexample -- a virtual container is not a container that travels.

## The plan, in dependency order

### Step 0 -- this document

Charter, measurement, and the open questions below. Ships review-needed.

### Step 1 -- make the sidecar travel (no code changes)

The containers are tracked; the fingerprint is not. Closing that is a
`.gitignore` decision and **it is the owner's**, because this tree's standing
rule is that `.gitignore` is not edited by a session. What this lane supplies is
the argument and the measurement, both above.

Open question for the owner: **41 containers currently ship without a
fingerprint. Do existing containers get one committed retroactively, or does the
rule apply going forward only?** Retroactive means minting 41 sidecars from the
current tables and trusting that the current tables are right -- which is the
same act the defect describes, done deliberately and once, with witnesses.

### Step 2 -- read the flag that is already written

**This step was rewritten after measurement.** It previously asked where currency
should be stored and offered three candidate homes. That question is void: the
storage exists in all three formats and is written today. The real question is
smaller and better posed:

**Why is the place currency already lives never consulted, and what should
consulting it do?**

Concretely, in dependency order:

1. **Give `CDX_HDRF_DIRTY` a WRITER, then a reader -- in that order.**
   *Re-measured 2026-09-06 and this item was backwards.* It is not "set and
   cleared and read nowhere"; `cdxfile::set_dirty` has zero callers, so the flag
   is always zero. A reader alone would check nothing while looking like a
   check. The CNX side shows the whole shape, both halves:

   - **written** by `cmd_pack.cpp:259` and `cmd_zap.cpp:222` through
     `cnxfile::set_dirty`, and raised directly around the save protocol at
     `src/xindex/cnx_backend.cpp:872`;
   - **read** at `src/xindex/cnx_backend.cpp:465`.

2. **Decide what a dirty container means at open. THE QUESTION IS SMALLER THAN
   THIS DOCUMENT ORIGINALLY POSED IT, because CNX already answered it and has
   been shipping the answer.** This item used to read as an open design
   question -- "the in-code principle says a stale index that answers is worse
   than one that refuses, but applied literally every unclean shutdown becomes a
   mandatory REINDEX". CNX resolved exactly that tension, and **not by
   refusing**. `src/xindex/cnx_backend.cpp:465`, after the document is known to
   load:

   ```
   if (container_is_dirty_(cnx_path_.string())) {
       std::cout << "[CNX DIRTY] container was not cleanly saved; rebuilding: " ...
       rebuild();
   }
   ```

   with the argument stated above it: an interrupted save left the directory
   pointing at the PREVIOUS blocks, which are intact, so this is **not repairing
   corruption -- it is discarding an ordering we cannot prove.** `close()`
   completes it: "The cost of losing this race is a rebuild, not a wrong answer."

   **So the owner ruling is now a yes/no, not a design.** Does CDX adopt CNX's
   answer -- rebuild at open, announced, after the container is proven to load --
   or does CDX differ?

   **The one measurable reason it might differ, and the crux the ruling turns
   on:** a CNX rebuild reloads in-process structures. A disk CDX is LMDB-backed,
   so its equivalent is a BUILDLMDB pass over the whole table. At the scale this
   engine has already been measured against (Pinocchio, 1M students / 5.5M
   enrollments) those are not the same cost, and an automatic rebuild at open is
   a very different promise there than on a four-row sandbox table. **That, and
   not the principle, is what the ruling has to weigh.** The principle is
   settled; the price is not.
3. **Decide whether `updated_ts` earns a comparison.** Per-tag freshness against
   the table's own modification time is the cheapest currency test available and
   costs no format change, because the field is already written. It is also the
   one most likely to produce false alarms, which is the argument against it.
4. ~~**`SNX_HDRF_DIRTY` is declared and never set.** Either wire it or delete
   the declaration.~~ **DISSOLVED 2026-09-06, re-measured.** Both options were
   void: SNX has no implementation to wire a flag into, and no `src/snx/`, no
   CMake target and no `.cpp` that includes its header. Every function it
   declares is a declaration with no definition. **This is deliberate** -- the
   header's own purpose block opens "Future custom compound index family (peer
   to CNX/CDX)". A specification written ahead of its implementation is not a
   promise broken. See the correction under the mechanism table. The only
   residue is one word of frontmatter: `status: supported` on a file whose prose
   says "Future".

### Step 3 -- a spec that can actually see it -- DONE 2026-09-06 (`403cb4072`)

Two hard constraints, both learned here:

- **It CANNOT use a RAM VFS fixture.** *Recorded first as: ramfs is
  sidecar-exempt, so a RAM-VFS fixture would assert nothing and go green. That
  understated it.* The owner's ruling makes the constraint stronger than
  "useless": **a vdisk cannot hold an LMDB-backed CDX at all**, because CDX falls
  back to "cnx" mode there. The fixture does not go green having asserted
  nothing -- it cannot be BUILT. The failure is at construction, not at
  assertion, and that is a better constraint to have written down because it
  cannot be worked around by a cleverer marker.
- **It must assert on FIELD VALUES**, per the `IDXSTALE` and `CNXLIVE` note that
  `RECNO()` and `FOUND()` render EMPTY in a `?` marker and `STR()` does not
  rescue them.

**Delivered as `IDXNAME`** (`index_field_name_resolution.dts`, 8 markers,
explicit-run until soaked; `kRegressionSpecs` 78 -> 79). Real on-disk container
under `DBF/SANDBOX`, all three path slots set explicitly, teardown that erases
the table, the `.cdx`, the `.cdx.meta` sidecar and the LMDB env together.

Every marker reads `TAILKEY` -- six bytes, no truncation, no alias -- so an arm
can only go green by landing on the right row. `IDXN_T3` is a three-way
discriminator: `T3` is the descriptor token finding its own field, `T2` is it
finding the OTHER field, `T1` is `SET ORDER` accepted and ignored.

**Two branches remain uncovered and are named in the spec rather than left to be
assumed:** the mangled `~n` token for two fields colliding at ten bytes, and the
rule that a logical name beats another field's token. Both need the same
collision, and `~` in a tag argument is an unmeasured question about the
tokenizer. They want a second cut; nothing else in the corpus covers them.

`kRegressionSpecs` is a hand-maintained `std::array<..., N>`; adding an entry
without bumping N is a hard compile error, which is the intended behaviour.

### Step 4 -- one implementation of tag -> field -- DONE 2026-09-06 (`403cb4072`)

*Recorded first as: "Collapse `field_index_for_tag_()` and
`activeTagFieldIndex1()` to a single implementation with the trimming and NUL
handling." Both halves of that sentence were wrong, and they were wrong in ways
worth keeping visible.*

**The count was two and it was five.** Measured across the tree:

| site | what it was |
| --- | --- |
| `index_manager.cpp` `activeTagFieldIndex1()` | upper-only; no trim, no NUL, no alias |
| `cdx_native_backend` `field_index_for_tag_()` | its own matcher |
| `cnx_backend` `field_index_for_tag_()` | a BYTE-FOR-BYTE copy of the above |
| `dbarea_adapt.cpp` `field_index_ci()` | a seventh-hand version |
| `cmd_buildlmdb.cpp` | its own `textio::ieq` loop |

**And "collapse to a single implementation" was the wrong instruction.** A
single implementation already existed -- `xfg::resolve_field_index_std`, called
by eleven files and by `REPLACE` itself. The work was not to invent a sixth
opinion for the index layer to share; it was to ROUTE the five onto the
authority that was already there. Writing "collapse" invited exactly the
outcome this lane keeps cataloguing: a new mechanism where a used one existed.

**One capability had to move INTO the shared resolver for the merge to be
lossless.** The CDX tag directory stores names in `char name[32]`, NUL-padded;
`trim_copy` strips only `isspace` and NUL is not `isspace`. The two retired
backend matchers handled that and the standard resolver did not, so
`field_name_core_` absorbs it. Deleting private copies without lifting what they
alone could do would have been a quiet downgrade wearing a cleanup's name.

Unblocks the `compute_next_numeric` index fast path in AIF-156.

## Two questions this lane deliberately leaves open

1. **Is an index whose currency is unknown an error, or a warning?** See step 2
   item 2 -- it is the ruling this lane most needs and the one it must not make
   for itself.
2. **Does the fingerprint belong to the container or to the pair?** Today it
   describes the TABLE and lives beside the INDEX. That is why it can be
   regenerated from the table, and why regenerating it destroys its value.
