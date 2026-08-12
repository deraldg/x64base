# Memo-Resident Mini-Databases -- Mechanism, Residence, and Lane Map (V1)

Status: **runtime-proven first increment (2026-08-11, build 18:35:35, first
try); this document is the owner-ordered deep record** -- "document the heck
out of it... how did we do it? where does it reside, what lanes does it cross
and affect?" Mechanism over chronology, per the same instruction.

Owner: member.derald. **Coworker of record: member.ai.claude.cowork** (owner
assignment 2026-08-12). Steward: member.ai.claude.cowork. Lane: AIF-070
(Virtual Workspaces & Memo-Resident Mini-Databases, external design intake
member.ai.grok.xai 2026-07-28, activated 2026-08-11).

Proof of the claim in one line: `REGRESSION RUN WORKSPACE_MINIDB` -- a
13-table database is saved INTO one memo field (94,200 B, byte-compare
verified as a unit) and stood up again on a clean RAM disk FROM that memo
(24 files, 92,139 B, 65.5 ms, zero disk reads).

---

## 1. What it is

A **mini-database** is a whole small database -- table bytes, native index
bytes, the posture that wires them, and the session state that positions
them -- carried as the payload of ONE memo field in the `WORKSPACES` catalog,
which is itself an ordinary x64 table. The database describing databases now
also CONTAINS them. Loading one requires no disk source: the memo is the
database's carrier, and the RAM VFS is its runtime residence.

This was the chartered destination of the AIF-070 intake from its first day.
Everything before it (postures in memos, self-location, RAM hydration,
session snapshots) was, in retrospect, the staging of its parts.

## 2. How it works -- the mechanism

### 2.1 The container format: MINIDB 1

Length-prefixed sections, no escaping, binary-safe by construction:

    MINIDB 1\n
    POSTURE <len>\n
    <len bytes: the DTSHEMA 3 posture text, WSID-stamped>
    FILE <len> <relative-path>\n
    <len bytes: raw file image>
    ...repeated per file...
    END\n

Design decisions, each with its reason:

- **Length prefixes, not delimiters.** DBF and CDX images contain every byte
  value including NUL and newline. A delimiter-scanned format would need
  escaping and could be broken by data; a length-prefixed one cannot. The
  memo store's payload-agnosticism -- runtime-proven by the memo-zoo harness
  on embedded-NUL and high-byte payloads BEFORE any binary cargo existed --
  is what makes raw DBF/CDX bytes legal cargo with no encoding layer.
- **Relative paths only** (`basename`, `indexes/basename`). A container
  carries no machine-specific location; the posture inside it is
  self-locating (DTSHEMA 3) and is re-pointed at the hydration target on
  load. The payload is portable by construction.
- **The posture rides INSIDE the container.** One artifact, one oracle pass,
  one token. The catalog row's SNAPSHOT field references the whole unit.
- **`MINIDB 1` is a FMT value, not a DTSHEMA version.** The catalog's FMT
  column was reserved for exactly this on the day the v2 schema was designed
  ("DTSHEMA 2 today, MINIDB n later"). The DTSHEMA namespace names posture
  formats; MINIDB names containers that EMBED a posture. This separation is
  the same one-format-one-writer discipline that the same day's DTSHEMA-name
  collision (AIF-078 D5/Q5, reconciled to DTWSSNAP 1) proved necessary.

### 2.2 The save path

`WORKSPACE SAVE <name> MEMO MINIDB` (trailing keywords, any order; MINIDB
implies v3, because the embedded posture must be self-locating to survive
re-pointing). In `ws_memo::save_to_memo` (src/cli/cmd_workspace.cpp):

1. WS_ID allocated (max+1 under the catalog FLOCK), prior live row of the
   name superseded, WSID `M<id>` stamped into the posture -- unchanged from
   the posture-only path; MINIDB is a carrier variation, not a new pipeline.
2. `build_minidb_container(posture, ...)` walks every OPEN area: the table
   file and, when an order is attached, the index file are read whole and
   appended as FILE sections. **Reads are residence-aware**
   (`read_all_bytes`): a source living in the RAM VFS is read through
   `xbase::ramfs::open`, not the OS -- so a RAM-resident working set can be
   saved whole, which is the owner's "save the state in the memo when we
   close" made literal.
3. The container goes through the SAME memo write and the SAME oracle as
   every posture save: `put_text`, then read back through the token stored
   IN THE FIELD and byte-compared. The oracle that was built for 1 KB
   postures verified a 94 KB binary container without modification. Derived
   catalog metadata (MAX_AREAS, SELF_REF) is measured from the POSTURE, not
   the container -- binary cargo is never keyword-scanned.
4. The catalog row records FMT = `MINIDB 1`. The row IS the registration;
   nothing about the payload is knowable only by parsing it.

### 2.3 The load path

`WORKSPACE LOAD <name> MEMO RAM` fetches the payload and sniffs the first
line. A `MINIDB 1` header routes to `hydrate_minidb`:

1. Sections are walked by length; FILE bytes are written into the mounted
   RAM VFS through `xbase::ramfs::open(create)` -- the same engine-honest
   streams as disk-sourced hydration, and the same rule: NEVER
   std::filesystem, which would land bytes on real disk while claiming RAM.
2. The embedded posture has its root lines stripped and RAM roots injected
   after the header -- the v3 self-location mechanism, reused unchanged as
   the hydration vehicle for the third time (broken-env restore, disk
   hydration, now memo hydration).
3. `schema_load_from_stream` stands the areas up; CURSOR/CURRENT lines in
   the posture restore session state; the final refresh slaves children.
   The hydration is timed and reports files/bytes/ms.

Guard: plain `WORKSPACE LOAD <name> MEMO` (no RAM) REFUSES a MINIDB payload
with the hydration instruction. Its tables have no disk home to open; a
half-load that stood up empty areas over missing files would be the silent
kind of failure this codebase spends its days hunting.

### 2.4 What the first measure said

Save: 94,200 B container = 92,139 B table+index bytes + 1,443 B posture +
~600 B section headers; oracle OK on the whole unit. Hydrate onto a CLEAN
RAM disk: 24 files, 65.5 ms, zero disk reads -- FASTER than the disk-sourced
hydration of the same files (71-94 ms measured the same afternoon), because
memo-to-RAM is memory-to-memory once the sidecar page is warm. Rows read,
CDX attached from memo-carried bytes through the native fallback (the LMDB
route correctly fails in RAM; see 5.4). VDISK census agreed with the
hydration counter byte-for-byte -- the independent cross-check held for
binary cargo exactly as it held for disk copies.

## 3. How it happened -- composition, not construction

The owner's observation mid-build: "everything I make uses the next thing I
make... it all fits together for free because I made everything from the
ground up." MINIDB is that sentence as an artifact. The feature added ~150
lines, and every hard problem in it had already been solved by a part built
for a different reason:

| Prior piece | Built for | What MINIDB took from it |
| --- | --- | --- |
| Serializer/loader split (AIF-070 M1) | zero-behavior-change refactor | a posture as a STRING, embeddable in anything |
| WORKSPACES catalog + oracle (M2/M3) | postures in memos | the write path, FLOCK, attribution, supersede versioning, the read-from-the-field oracle |
| Memo-zoo harness | orthogonality stress | the PROOF that binary payloads are safe, before any existed |
| DTSHEMA 3 self-location | env-first fragility | the re-pointing mechanism that makes an embedded posture land anywhere |
| ramfs (AIF-043) | in-memory tables | the engine-honest byte sink and the residence test |
| RAM hydration + timing | the 2x2 carrier/residence matrix | the hydrate loop, the census cross-check, the ms discipline |
| Session state (CURSOR/CURRENT) | "resume exactly here" | rides free inside the embedded posture |
| GPS | cursor reporting | the position verifier for what rides free |

Nothing on that list was designed for MINIDB. The container format and the
sniff-and-route are the only new inventions, and both are small. This table
is the documentation the owner asked for when asking "how did we do it": by
having already done it, in pieces, each proven alone.

## 4. Where it resides

### 4.1 In source

- `src/cli/cmd_workspace.cpp` -- the whole feature: `read_all_bytes`
  (residence-aware), `build_minidb_container`, `hydrate_minidb`, the MINIDB
  sniff in `hydrate_to_ram` and the refusal in `load_from_memo`, the
  `MINIDB` keyword in the SAVE dispatch, FMT stamping in `save_to_memo`.
- `src/memo/memostore.cpp` -- unchanged. The carrier needed no modification
  to carry databases; that is the payload-agnosticism thesis, cashed.
- `include/xbase/ramfs.hpp` -- unchanged. The byte sink was already correct.
- `dottalkpp/data/scripts/workspace_minidb.dts` + `cmd_regression.cpp` spec
  42 (`WORKSPACE_MINIDB`) -- the standing proof.

### 4.2 On disk (and off it)

- Container bytes: the `WORKSPACES` memo sidecar (DTX store) in the
  workspaces root -- disk-resident, append-new semantics, one token per
  save.
- Registration: the `WORKSPACES.dbf` row -- WS_ID, WSID-stamped identity,
  FMT `MINIDB 1`, SIZE_B, dims, lineage. The catalog is the only index of
  what exists; there is deliberately no second registry to drift.
- Hydrated instance: the RAM VFS only. It dies at `VDISK UNMOUNT` by
  design -- the memo is durable, the instance is ephemeral, and the gap
  between them is the chartered writeback cycle.

## 5. Lanes crossed and affected

- **AIF-070** (home lane): the chartered destination is now runtime-proven
  in first increment. The Grok whitepaper reconciliation is STILL OWED and
  now matters more, not less -- the built thing must be read against the
  design that chartered it (illustrated extended DTSHEMA, per-area kind,
  memo-bytes -> hydration) and divergences recorded. Constraint check:
  memos stayed payload-agnostic (the container is a CONVENTION over an
  agnostic store, not a store feature); destructive `WORKSPACE OPEN`
  untouched; BBS lane untouched.
- **AIF-078 / multi-workspace addressing**: a MINIDB hydrates into the ONE
  flat area set. Two mini-databases cannot co-reside today for the same
  reasons two workspaces cannot (first-match name resolution; flat RAM
  root). The co-residency findings recorded in the AIF-070 row apply
  verbatim, and the per-workspace RAM subroot decision should be made
  BEFORE anyone hydrates two containers.
- **AIF-079 (declared-but-unimplemented)**: MINIDB deliberately declares
  nothing it does not do. No compression flag, no checksum-per-file, no
  encryption byte reserved "for later" -- absent capabilities are absent
  from the format, so v2 of the container can ADD sections (the loader
  ignores unknown section kinds loudly) rather than un-lie about v1.
- **AIF-082 6.10 / AIF-083 F5 (memo-width work)**: those lanes want 64-bit
  memos for BBS bodies; this lane now demonstrates the memo store carrying
  ~94 KB units routinely. The three-lanes-one-piece-of-work note in the
  AIF-070 row gains a fourth interested party: a mini-database posted to a
  BBS board would be a database SENT AS A MESSAGE -- the owner's "we can't
  share unless we write it or send it," second half.
- **Memo-zoo charter**: M2a (contention) now guards real value -- catalog
  rows carrying whole databases. M2b (RAM-VFS-resident memo store) is the
  remaining leg of "RAM memo": today the CONTAINER hydrates to RAM but the
  memo store it came from is disk-resident (the DTX-sidecar-bypasses-ramfs
  finding, corrected the same day).
- **Part B (MCC regeneration with NOTES M)**: the container did NOT
  originally carry memo sidecars, because no MCC table has one -- a NAMED
  COUPLING at authoring time. **RESOLVED from the engine side 2026-08-12**
  (owner: "minidb sidecar carriage"): `build_minidb_container` now asks
  each area's attached backend for its own file (`IMemoBackend::path()`,
  flushed before capture) -- better than the predicted "learn the naming
  convention," because the backend simply names itself. Hydration lands
  sidecars on the REAL filesystem under the mount dir (deliberately: the
  DTX layer bypasses the ramfs and would never see a VFS-resident
  sidecar). Proof: DB_T3/DB_T4 in `workspace_minidb.dts`, residue-hardened
  by poisoning the live sidecar post-save so a green can only come from
  container bytes. Part B's remaining half is the fixture side: MCC
  flavors regenerated with NOTES M so the CANONICAL workspace exercises
  this path, not just the regression's throwaway table.
- **Writeback lane -- RULED 2026-08-12, ready to build.** A hydrated
  mini-database that returns to DISK is a database EXTRACTED from a memo --
  the export direction. Writeback and MINIDB together close the full cycle:
  disk -> memo -> RAM -> disk. Three owner rulings, all settled:

  1. **Verb: `WRITEBACK`** (owner choice over PERSIST and FLUSH). Pairs with
     the already-settled `DISMISS` for the discard side. `COMMIT` was
     rejected earlier: it collides with the table-buffer transaction verb,
     and a workspace-level persist is a different act from a record-level
     commit. FLUSH was rejected for the same class of reason -- in this
     engine it reads as "drain a buffer to its existing home", not
     "materialize a RAM/memo workspace onto disk".
  2. **Compaction: a deliberate `WORKSPACE COMPACT` verb.** Supersede keeps
     retaining prior payload bytes by default (history is free; ten saves of
     a 94 KB container hold ~1 MB), and space is reclaimed only when the
     owner asks for it. Rejected: automatic erase-on-supersede, which would
     make every save silently unrecoverable to its predecessor. `MemoStore::
     erase` is the mechanism and is zoo-proven; `PREV_ID` lineage survives
     compaction either way, so COMPACT frees bytes without erasing the
     record that the history existed.
  3. **Content type: BOTH homes, with the `FMT` column AUTHORITATIVE.** The
     spec s24 write-call parameter records intent at write time and travels
     with a payload carried outside the catalog; the catalog's `FMT` column
     ('DTSHEMA 2', 'MINIDB 1') is what readers TRUST. The redundancy is
     deliberate, so the disagreement rule must be written and enforced, not
     assumed: **when they differ, FMT wins, and the mismatch is reported
     rather than silently resolved** -- a payload whose self-declaration
     disagrees with its catalog row is exactly the shape of a half-written
     save, and this lane's whole history says such things must be loud.

  Build order implied by the rulings: `WRITEBACK` first (it is the missing
  half of the cycle and has a proven inverse to test against), `WORKSPACE
  COMPACT` second (it needs writeback to be meaningful -- you compact after
  you have somewhere else to stand), the FMT disagreement check third (cheap,
  but it wants both of the above to exist before it has anything to guard).

## 6. Honest non-claims and limits

- **No multi-file atomicity.** The container is written in one memo put and
  verified as one unit -- that IS atomic at the carrier level -- but
  hydration writes N RAM files sequentially; a mid-hydration failure leaves
  a partial RAM set. Acceptable today because the RAM set is disposable by
  definition; becomes real when writeback lands.
- **No LMDB carriage.** Out of scope by the ramfs contract (LMDB must mmap
  a real OS file) and by owner rule ("lmdb only for disks"). CDX orders
  attach in RAM through the native fallback; the LMDB route fails there
  correctly and loudly.
- **Memo-sidecar carriage landed 2026-08-12** (engine side; see Part B
  bullet above). Honest residual: a hydrated sidecar is DISK-resident
  under the mount dir, not VFS-resident -- unavoidable until ramfs
  memo-store coverage lands -- and it survives unmount as residue
  (truncate-overwritten by the next hydration of the same name).
- **No size governance yet.** SIZE_B records what a container weighs;
  nothing yet refuses a save that would dwarf the sidecar or the RAM
  budget. EST_HYD_B and the vdisk Layer-2 budget are the chartered seams.
  Related growth fact, stated plainly: supersede does NOT erase the old
  token's bytes, so ten saves of a 94 KB container retain ~1 MB in the
  sidecar. `MemoStore::erase` exists and is zoo-proven; a compaction /
  supersede-erase policy is a chartered decision, not an oversight --
  history-keeping vs space is the owner's call, and PREV_ID lineage means
  erasing bytes need not erase the record of lineage.
- **PAYLOAD_SHA still chartered.** The oracle verifies at save; nothing
  re-verifies a container years later. VERIFIED_AT waits for WORKSPACE
  VERIFY.

## 7. Evidence

| Claim | Evidence |
| --- | --- |
| database in a memo, verified as a unit | build 18:35:35 hand run: mcc_db 94,200 B, oracle byte-compare OK |
| hydration from memo, zero disk reads | same run: 24 files / 92,139 B / 65.5 ms onto a clean RAM disk; VDISK census byte-identical |
| rows + indexes usable from memo-carried bytes | DB_T1 (STUDENTS row), DB_T2 (ENROLL CDX TAG SID) both .T. |
| repeatable | `REGRESSION RUN WORKSPACE_MINIDB` (spec 42), self-authoring, self-erasing |
| binary safety inherited, not asserted | memo-zoo: 20,500 generations / 104,044 ops / embedded NULs / 0 divergences, run BEFORE binary cargo existed |

## 8. Open questions (the pondering, kept)

1. **Compaction policy** -- do superseded MINIDB tokens get erased, and on
   whose ruling? (Growth math in 6; lineage survives either answer.)
2. **Size ceiling** -- strict first, then dynamic (owner's growth-limiter
   doctrine): what refuses a 500 MB container, and does it refuse at save
   or at hydrate?
3. **Sharing by send** -- a container is a portable database; the natural
   transports are a file export of the memo payload and, once memo-width
   lands, a BBS post. Both are design-only today.
4. **Two containers co-resident** -- blocked on the multi-workspace lane's
   subroot + name-scope decisions; do not build around it.
5. **Container v2 candidates** -- per-file checksums, optional compression,
   memo-sidecar sections (Part B), LMDB export stubs. Each must be a new
   section kind, never a reinterpretation of v1.

---

*This document is the mechanism record. The intake row (AIF-070,
`AI_INTERACTION_INTAKE_QUEUE_V1.md`) is the registration; the regression
spec text is the operational summary; the white paper
(`WHITE_PAPER_X64_OOP_MEMO_V1.md`) holds the memo-store design this rides
on. Per the pointer-over-copy rule, none of the four restates another's
whole.*
