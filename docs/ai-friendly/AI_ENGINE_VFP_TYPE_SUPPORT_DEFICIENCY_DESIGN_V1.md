# Engine VFP field-type support deficiency -- charter + PDLC (v1)

Status: **design-only (review-needed).** Authored in a mounted sandbox that cannot
build or run the engine; every code claim below is read from source, not compiled.
All build + proof steps are maintainer-operated handoffs.

Owner of record: `member.derald`
Lane owner / author: `member.ai.claude.cowork` (assigned this lane 2026-08-07)
Coworker: `member.ai.grok` (external advisor; contributes via the BBS / external-AI
intake channel, harvested + curated per `MONITOR_HARVEST_CURATE_EXTERNAL_AI_V1.md`)
Lane / ticket: **AIF-091** (lane `dbf-vfp-type-support`, claimed 2026-08-07 via
`tools/coordination/session_coordinator.py claim-aif`, run_id `COWORK-20260807-002`;
ledger: `coordination/aif/AIF-091.claim`).
Prior art read (source, not compiled): `src/xbase/dbf_create.cpp` (`supports_type_now`),
`include/xbase_field_getters.hpp`, `include/xbase_vfp.hpp`, `include/xbase/field_codec.hpp`,
`src/cli/cmd_create.cpp`, and the dBASE 7 spec (external, sibling format -- out of scope,
see history note below).

## 1. Deficiency statement

On the FoxPro/VFP branch (the lineage this engine actually follows -- not dBASE
Level 7, which is a separate Windows-era fork), VFP field-type support is
incomplete in three graded ways:

1. **Nullability is not decoded (highest impact).** ~~`include/xbase_vfp.hpp` reads a
   field's declared `nullable` flag (bit `0x02`)~~ **CORRECTED 2026-09-04: IT DID NOT
   READ THE FLAG AT ALL, AND THIS DEFICIENCY WAS WORSE THAN ITS OWN CHARTER SAID.**
   `VfpField::flags` sat at BYTE 23 -- the autoincrement STEP value -- while the
   format puts field flags at BYTE 18 (Microsoft, Table File Structure; Hentzen et
   al. s1c2, "bit 0 of byte 18"). The struct was a faithful dBASE III descriptor
   (work-area id at 20, SET FIELDS flag at 23) wearing a VFP name, so
   `nullable = flags & 0x02` read bit 1 of the step byte and the real flags byte was
   swallowed inside `reserved1`. Nothing caught it because every VFP- and x64-flavor
   table in this repository carries ZERO at byte 18 AND ZERO at byte 23 (measured,
   21 tables): the wrong byte and the right byte agree on every file we own, so the
   decoder was correct by coincidence and would have gone silently wrong on the
   first real nullable table -- the AIF-123 shape. Fixed with compile-time offset
   asserts plus a runtime decoy test; `0x64` now reads the same byte, which it has
   always carried by inheriting the descriptor shape. There is still NO decoder for the
   per-row null bitmap that VFP stores in the hidden `_NullFlags` system column
   (field type `0`), and NO handling of the `system` field flag (bit `0x01`).
   Consequences: (a) the engine cannot tell which rows are actually NULL; (b) the
   `_NullFlags` column is surfaced as a junk binary data field instead of being
   skipped; (c) nullable fields cannot be created. Nullable columns are pervasive in
   real VFP data, so this is a correctness gap, not an edge case.
2. **Varchar `V` is read-only and un-trimmed.** `xbase_field_getters.hpp` decodes
   `V` as textual, but `supports_type_now` (dbf_create.cpp:637-654) does NOT list
   `V`, so it cannot be created; and the variable-length trimming (true length lives
   in the varlength bits / trailing length byte) is not applied, so read values can
   carry trailing padding.
3. **Varbinary `Q`, Blob `W`, General `G`, Picture `P` are absent.** Neither read
   (fall through getter defaults to blank/raw) nor create (rejected by
   `supports_type_now`).

## 2. Evidence (source-verified)

- Creatable per flavor (`dbf_create.cpp` `supports_type_now`): MSDOS/FOX26 =
  `C N F D L M`; VFP/X64 = `C N F D L M I B Y T`. Anything else is rejected with a
  clean `CREATE: field type '<T>' ...` error (fails closed -- no corruption).
- Readable (`xbase_field_getters.hpp` predicates): `C V M N F I Y B D T L`
  (adds `V` over the creatable set -> the read/create asymmetry).
- VFP field flags decoded (`xbase_vfp.hpp:238-239`): `nullable = flags & 0x02`,
  `binary = flags & 0x04`. NOT decoded: `system = flags & 0x01`, varlength bits.
  **CORRECTED 2026-09-04 -- THIS LINE WAS THE MOST WRONG THING IN THE DOCUMENT, and
  it is left standing because it is the evidence of how the defect hid.** Those two
  expressions were reading BYTE 23, not the flags byte at 18, so neither `nullable`
  nor `binary` was ever decoded correctly for any flavor. The autoincrement members
  next to them (`ex.autoincrement`, `next_autoinc`, `step_autoinc`) were assigned
  constant zero, because the struct had no members at the offsets those values live
  at. `system` is now decoded, autoincrement is decoded from `0x0C` AND EXCLUDED FROM
  BINARY (0x0C carries the 0x04 bit, so a naive `& 0x04` calls an autoincrementing
  column binary), and `0x64` reads the flags byte it has always carried. Guarded by
  `src/tests/test_vfp_field_descriptor.cpp` and by compile-time `offsetof` asserts.
- Extensibility seam already exists: `include/xbase/field_codec.hpp`
  `register_field_type(char, Codec, FieldTypeMeta)` is "the single extensibility
  seam ... so the chain never needs a per-type switch edit" (built-in demo type `X`
  in `field_codec.cpp`). New types land as registered codecs, not core edits.

## 3. Scope and non-goals

In scope: the VFP-branch types above, on all VFP/X64 read+write paths, plus the
`_NullFlags` / `system` column mechanics.

Out of scope (recorded, not chosen): dBASE Level 7 types `@` Timestamp, `O` Double,
`+` Autoincrement, and `B`-as-Binary. These are a sibling Windows fork (Visual dBASE
7, 1997), not the FoxPro/VFP lineage; last true MS-DOS dBASE was dBASE 5.0 for DOS
(1994) and its format is already covered as the classic `0x03`/`0x83` flavors. Do
not conflate MS-DOS dBASE with dBASE 7.

## 4. PDLC (phased; each milestone runs design -> build -> prove -> accept gate)

Phase 0 -- **Charter + claim.** This doc + host-side `claim-aif` + intake/registry
entry. (This document.)

Milestone M1 -- **Nullability + `_NullFlags` / system column (priority 1).**
- Decode the `system` field flag; exclude system columns from the user field set.
- Decode the `_NullFlags` bitmap column into per-row null state; expose `ISNULL()`-
  equivalent and NULL-aware getters.
- Support creating nullable fields (allocate/maintain the `_NullFlags` column).

Milestone M2 -- **Finish Varchar `V` (priority 2).**
- Apply varlength trimming on read; add `V` to `supports_type_now`; round-trip create.

Milestone M3 -- **Varbinary `Q` + Blob `W` via the codec registry (priority 3).**
- Register codecs through `register_field_type`; wire memo/block storage for `W`.

Milestone M4 -- **General `G` / Picture `P` (priority 4, optional).**
- Legacy OLE embedding; implement only if OLE interop is required.

Each milestone's **accept gate**: round-trip proof (create -> write -> read-back
equals input) on the VFP/X64 flavors, plus a decode proof against a real VFP fixture
carrying the type; recorded as a proof run under `labtalk/proofs/runs/`.

## 5. Test plan

- Round-trip canary per type: `CREATE VFP` / `CREATE X64` a table with the type,
  APPEND/REPLACE known values, read back, assert equality (a `.dts` under
  `dottalkpp/data/scripts/`).
- Null-decode fixture: a known VFP table with nullable + `V`/`Q`/`W` fields (external
  fixture) read and asserted against expected NULL/value map. Fixtures tracked per
  the "keep the proof always" ruling; never `.mdb`.
- Negative canary: confirm CREATE still fails closed on any not-yet-supported type.

## 6. Coordination

- Owner/steward: `member.ai.claude.cowork` (this lane). Coworker `member.ai.grok`
  contributes design review + type-decode proposals via the external-AI intake
  channel; harvest each Grok submission into a RUN + ENVELOPE + INDEX_ENTRY and curate
  into this AIF (per `MONITOR_HARVEST_CURATE_EXTERNAL_AI_V1.md`; the index-completeness
  gap noted there applies -- index every submission, not just one).
- Host-side handoffs: `claim-aif` (assign the number + write `coordination/aif/AIF-NNN.claim`);
  add the intake-queue row; register the project in `labtalk/registries/` if this
  becomes a tracked project lane. All builds + proof runs are maintainer-operated.

## 7. Risks

- Record-layout math: mis-handling the `_NullFlags` / varlength columns shifts every
  downstream field offset. Gate M1 on a byte-exact round-trip before trusting reads.
- Symbol collisions with the dBASE branch (`B`, `I`) are out of scope here but must be
  flavor-gated if dBASE-7 read is ever added -- cross-reference, do not solve here.
