# Engine VFP M1 -- _NullFlags decode design (v1)

Status: **design-only (review-needed).** Sandbox-authored; code claims read from
source, external format claims cited below. Build + proof are maintainer handoffs.

Owner: `member.ai.claude.cowork`   Coworker: `member.ai.grok`   Owner of record: `member.derald`
Parent: `AI_ENGINE_VFP_TYPE_SUPPORT_DEFICIENCY_DESIGN_V1.md` (AIF-NNN), milestone M1.
The `_NullFlags` / varlength format facts in section 2 are NOT from the x64base source
tree; they are drawn from the external references credited in section 9.

## 1. What M1 delivers

Correct NULL semantics and correct varchar/varbinary length on the VFP/X64 read+write
paths, by decoding the two things the engine currently ignores: the **`system` field
flag** and the **`_NullFlags` system column**.

## 2. The format (authoritative)

VFP tables that use nullable and/or variable-length fields carry one extra, hidden
field: **`_NullFlags`**, field type **`0`**, marked with the **system** flag
(field-descriptor flags byte, bit `0x01`). The engine today reads flags `0x02`
(nullable) and `0x04` (binary) but NOT `0x01` (`xbase_vfp.hpp:238-239`), so the column
is neither recognized as system nor decoded.

`_NullFlags` holds a **bitmap**, length = `ceil(bits / 8)` bytes, with bits assigned
in **physical field order**. Each field can contribute:

- a **null bit** if the field is nullable (flag `0x02`), and
- a **varlength bit** if the field is variable-length (`V` Varchar / `Q` Varbinary).

A field that is both nullable and varchar contributes **two** bits. Bit meanings:

- **Null bit = 1** -> the field's value in this row is NULL.
- **Varlength bit = 1** -> the value does NOT fill the field; its true length is stored
  in the field's **last data byte**, content occupies `[0 .. len-1]`, remainder is
  padding. **Varlength bit = 0** -> the field is full-width (use the whole field).

Version-byte tie-in: `0x30` VFP, `0x31` VFP+autoincrement, `0x32` VFP with
Varchar/Varbinary/Blob (already in `detectDbfLevel`).

## 3. Decode algorithm (read path)

1. **Partition fields.** While loading the field descriptor array, read flag `0x01`;
   route any `system` field (the `0`/`_NullFlags` column) to a hidden slot, NOT the
   user field vector. Record its record-offset + length.
2. **Build the bit map.** Walk user fields in physical order; assign the next bitmap
   bit index to each field's null bit (if nullable) then its varlength bit (if V/Q).
   Persist the per-field `(null_bit_index?, varlen_bit_index?)`. (Bit-assignment
   ORDER is the one ambiguity across implementations -- see risk R1; gate on a fixture.)
3. **Per row:** read the `_NullFlags` bytes at its offset. For each field:
   - if it has a null bit and that bit is set -> value is NULL (short-circuit).
   - else if V/Q with a varlength bit: length = bit set ? `last_field_byte` :
     `field_length`; decode content `[0 .. length-1]`.
   - else decode by existing type codec.
4. Expose NULL through a null-aware getter + an `ISNULL(field)`-equivalent; keep the
   existing getters returning the decoded value for non-null rows.

## 4. Write path (create + update)

- **CREATE nullable / V / Q:** append the hidden `_NullFlags` `0`/system field sized to
  `ceil(total_bits / 8)`; set flags `0x01` on it, `0x02`/varlength on the members.
  Bump the version byte to `0x32` when any V/Q/Blob field exists.
- **APPEND/REPLACE:** on write, set/clear each field's null bit and (for V/Q) its
  varlength bit + last-byte length; keep the bitmap and the row in sync in one place.
- Add `V` (and later `Q`) to `supports_type_now`; keep CREATE fail-closed for the rest.

## 5. Where it lands in the code

- Flag `0x01` decode + system-field partition: `xbase_vfp.hpp` field loop (beside the
  existing `0x02`/`0x04` reads at 238-239).
- Bitmap model + null-aware getters: `xbase_field_getters.hpp` (new null-aware entry
  points; existing predicates unchanged).
- Codec seam for V/Q: `register_field_type` (`include/xbase/field_codec.hpp`) -- no core
  switch edits, per its stated contract.
- CREATE acceptance: `supports_type_now` (`src/xbase/dbf_create.cpp:637-654`).

## 6. Accept gate (proof, maintainer-run)

- **Byte-exact round-trip:** `CREATE VFP`/`X64` a table with a nullable `N`, a nullable
  `V`, and a non-null full-width `V`; APPEND rows incl. NULLs and short varchars;
  read back; assert the null map + exact string lengths; re-open the written file in
  a second process and re-assert (the shared-store restart rule).
- **Real-fixture decode:** read a known VFP `0x32` table (external fixture, tracked;
  never `.mdb`) with nullable + V/Q fields; assert against an expected null/value map.
- **Negative:** CREATE still fails closed on `G`/`P`/`W` until their milestones land.
- Record both under `labtalk/proofs/runs/`.

## 7. Risks

- **R1 -- bit-assignment order.** Implementations differ on whether all null bits
  precede all varlength bits, or bits interleave per field. This spec assumes
  per-field interleave (null then varlength, walking fields in order). **Do not ship
  M1 on the assumption alone** -- the real-fixture proof (6) is what fixes the order;
  encode it as a single documented function so a flip is one edit. Good task to hand
  Grok: verify the order against several real VFP tables and report the bit map.
- **R2 -- offset math.** The `_NullFlags` column consumes record bytes; mis-sizing it
  shifts every field offset. Gate on the byte-exact round-trip before trusting reads.
- **R3 -- `0x32` gating.** Writing V/Q without bumping the version byte to `0x32`
  produces a file VFP will reject; assert the version byte in the round-trip.

## 8. Coworker (Grok) task seam

First concrete external-AI ask, harvested into the AIF: **confirm the `_NullFlags`
bit-assignment order (R1) against real VFP `0x30`/`0x31`/`0x32` tables** and return the
observed per-field bit map. Route via the BBS/external-AI intake; harvest to
RUN + ENVELOPE + INDEX_ENTRY; curate the finding into the M1 decode function.

## 9. Sources (external format references -- credited)

**Publish plan:** these credits stay here in the dev docs while the lane is in
progress. They publish to the website `third-party-acknowledgements` page as part of
this feature's full-stack push -- NOT as a real-time site edit -- so the public credit
ships when the feature does and the site never drifts ahead of the source.

The `_NullFlags` and varchar/varbinary length mechanics in section 2 are derived from
these public references, not from the x64base source tree. They are third-party
community documentation of Microsoft's Visual FoxPro on-disk format; credit to their
authors, and any conflict between them is resolved by the real-fixture proof (section 6):

- Whil Hentzen et al., "The Hacker's Guide to Visual FoxPro" (hackfox), section 1
  chapter 2 "DBF, FPT, CDX, DBC -- Hike!": https://hackfox.github.io/section1/s1c2.html
- go-foxpro-dbf (Sebastiaan Klippert), issue #9 "Support VFP Varchar field" -- the
  `_NullFlags` varlength-bit + last-byte length behavior:
  https://github.com/SebastiaanKlippert/go-foxpro-dbf/issues/9
- tDBF (Delphi/BCB) open-discussion thread "_NullFlags Field on Visual FoxPro":
  https://sourceforge.net/p/tdbf/discussion/107245/thread/86bf22be/
- Microsoft, "What's New in Visual FoxPro 9.0", chapter 9 "New Data and Index Types":
  http://foxcentral.net/microsoft/WhatsNewInVFP9_Chapter09.htm
- dbfread, "Field Types" (type-code reference incl. `0`/`_NullFlags`):
  https://dbfread.readthedocs.io/en/latest/field_types.html

For the dBASE-7 history + the branch split (parent charter, section 3 non-goals):
dBASE (Wikipedia) https://en.wikipedia.org/wiki/DBase ; WinWorld dBASE 5.x
https://winworldpc.com/product/dbase/v ; .dbf format https://en.wikipedia.org/wiki/.dbf ;
and the dBASE 7 table spec examined this session:
https://www.dbase.com/Knowledgebase/INT/db7_file_fmt.htm
