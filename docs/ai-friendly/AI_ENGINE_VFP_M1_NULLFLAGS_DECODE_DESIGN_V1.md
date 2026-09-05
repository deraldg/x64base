# Engine VFP M1 -- _NullFlags decode design (v1)

Status: **design-only (review-needed).** Sandbox-authored; code claims read from
source, external format claims cited below. Build + proof are maintainer handoffs.

Owner: `member.ai.claude.cowork`   Coworker: `member.ai.grok`   Owner of record: `member.derald`
Parent: `AI_ENGINE_VFP_TYPE_SUPPORT_DEFICIENCY_DESIGN_V1.md` (AIF-091), milestone M1.
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

> **MEASURED 2026-09-04 PM -- VFP WRITES `0x05`, NOT `0x01`.** In
> `tools/vfp/fixtures/nullfix.DBF`, authored inside Visual FoxPro 9, the `_NullFlags`
> descriptor carries **`0x05` at byte 18 -- system AND binary**. Reading is unaffected
> (`decode_field_flags()` reports both bits, and the partition tests on `0x01`, which is
> present in `0x05`). **The write path is affected: see section 4.** The sentence above
> is left as written because it is what the CREATE instruction in section 4 was derived
> from.

`_NullFlags` holds a **bitmap**, length = `ceil(bits / 8)` bytes, with bits assigned
in **physical field order**. Each field can contribute:

- a **null bit** if the field is nullable (flag `0x02`), and
- a **varlength bit** if the field is variable-length (`V` Varchar / `Q` Varbinary).

A field that is both nullable and varchar contributes **two** bits, and **THE FULL/VARLENGTH
BIT IS THE LOWER OF THE TWO** -- Microsoft, *What's New in Visual FoxPro 9.0* ch. 9: "If a
field is both nullable and Varchar or Varbinary, two bits are used to represent a field.
The lower bit represents the 'full' status and the higher bit represents the null status."
Bit meanings:

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
   bit index to each field's **varlength bit (if V/Q) FIRST, then its null bit (if
   nullable)**. Persist the per-field `(varlen_bit_index?, null_bit_index?)`.
   **CORRECTED 2026-09-04, AND THIS IS THE ONE LINE R1 WAS ABOUT.** This step used to
   read "null bit (if nullable) then its varlength bit (if V/Q)", which is the
   OPPOSITE of what the format's author documents (section 2, quoted). It was an
   assumption, this document said "do not ship M1 on the assumption alone", and it was
   wrong. The order now lives in exactly one place in code --
   `include/xbase/vfp_null_bits.hpp`, `assign_null_bits()` -- as this document
   instructed, so a future flip is one edit and one test.
3. **Per row:** read the `_NullFlags` bytes at its offset. For each field:
   - if it has a null bit and that bit is set -> value is NULL (short-circuit).
   - else if V/Q with a varlength bit: length = bit set ? `last_field_byte` :
     `field_length`; decode content `[0 .. length-1]`.
   - else decode by existing type codec.
4. Expose NULL through a null-aware getter + an `ISNULL(field)`-equivalent; keep the
   existing getters returning the decoded value for non-null rows.

## 4. Write path (create + update)

- **CREATE nullable / V / Q:** append the hidden `_NullFlags` `0`/system field sized to
  `ceil(total_bits / 8)`; ~~set flags `0x01` on it~~ **set flags `0x05` on it (system
  `0x01` | binary `0x04`) -- measured from a VFP-authored file 2026-09-04; writing
  `0x01` produces a column VFP does not mark the way VFP marks its own** -- and
  `0x02`/varlength on the members. Bump the version byte to `0x32` when any V/Q/Blob
  field exists.
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
  **PARTIALLY MET 2026-09-04 PM by `tools/vfp/fixtures/nullfix.DBF`**, in two tests that
  deliberately do not overlap:
  - `dottalkpp_vfp_nullfix_r1a_test` parses the file BY HAND and grades the **format** --
    which bit means what, in which order. It must not ask the loader what the loader
    thinks, so it does not use it.
  - `dottalkpp_vfp_real_fixture_flags_test` reads the same file **through
    `vfp_loader::readFields` and `DbArea::partitionTrailingSystemField`** and grades the
    **decode path**: the partition, the field set, the nullable count, and the record
    offset cross-checked against the `displacement` VFP itself wrote.

  **STILL OWED ON THIS LINE:** the per-row bitmap read THROUGH THE GETTERS, so a caller
  asking for a value on row 2 is told it is null. That does not exist yet -- there is no
  null-aware getter -- so this gate is **not closed**.
- **Negative:** CREATE still fails closed on `G`/`P`/`W` until their milestones land.
- Record both under `labtalk/proofs/runs/`.

## 7. Risks

- **R1 -- bit-assignment order. ANSWERED FROM THE PRIMARY SOURCE 2026-09-04, AND THE
  ANSWER INVERTED THIS SPEC'S ASSUMPTION.** The original text read: *"This spec assumes
  per-field interleave (null then varlength, walking fields in order). Do not ship M1
  on the assumption alone."* Per-field interleave was right. The pair order was not.
  Microsoft's *What's New in Visual FoxPro 9.0* ch. 9 -- a source this document already
  cited in section 9 -- states the **lower** bit is "full" status and the **higher** is
  null status; Hentzen et al. confirm the walk is "in the physical order of the fields
  in the table". Encoded once in `include/xbase/vfp_null_bits.hpp` and guarded by
  `src/tests/test_vfp_null_bits.cpp`, whose Arrangement-A discriminator reads `0x04`
  under the corrected order and `0x02` under the old one. **Mutation-tested: flipping
  the two lines in `assign_null_bits()` reds 10 expectations, and the single-bit fields
  stay green -- the exact blast radius of the defect.**
- **R1a -- ANSWERED 2026-09-04 PM. THE FIXTURE EXISTS AND IT AGREED.**
  `tools/vfp/fixtures/nullfix.DBF` was created inside Visual FoxPro 9 by
  `tools/vfp/make_nullfix.prg`: version `0x32`, `id N(4) NULL`, `vname V(10) NULL`,
  `vfull V(10)`, `plain C(5)`, three rows chosen to separate the cases. Its three
  `_NullFlags` bytes came back **`0x02`, `0x0F`, `0x08`** -- three of the bytes
  `test_vfp_null_bits.cpp` Arrangement A had already asserted from the documentation,
  on a file nothing in this tree wrote. Guarded by
  `src/tests/test_vfp_nullfix_r1a.cpp` (target `dottalkpp_vfp_nullfix_r1a_test`); a missing fixture is a **configure-time
  FATAL_ERROR**, not a skip.
  - **The varlength bit is set when the field is NOT full** -- when the trailing length
    byte is in use. Rows 1 and 3 alone are ambiguous (the inverted polarity with the two
    varlength bits exchanged fits both); **row 2 settles it**, because both Varchar
    fields carry a length byte there and both bits are SET.
  - **`assign_null_bits()` and `varlength_value_length()` were already correct.** What
    was wrong was the prediction written into `make_nullfix.prg`'s header before the
    run, which inverted the polarity. That comment is left standing with the measured
    bytes beside it.
  - **The R1a fixture is built wrong in one place** and R1c below records it.
  - THE ORIGINAL RISK TEXT, kept because it is the record of what was believed, and
    because its first sentence was already false when written (the `*.dbf` glob missed
    the `.SCX`/`.VCX` tables VFP also writes -- re-measured by magic byte in
    `7a46a4a01`: 59 tracked DBF-format files, seven disagreeing):
    > **R1a -- THE FIXTURE PROOF IS STILL OWED, AND CANNOT BE RUN TODAY.** Measured
    > 2026-09-04: **21 VFP-flavor tables exist in this repository (13 tracked, 8 untracked),
    > every one version `0x30`, every one with ZERO nullable fields and ZERO system
    > fields.** There is no `_NullFlags` column anywhere in the tree, so the section-6
    > accept gate's "decode proof against a real VFP fixture" has nothing to decode. The
    > Grok seam (section 8) was never answered. **CONSEQUENCE FOR HOW M1 IS PROVEN:** a
    > create-then-read round trip cannot settle the layout, because our encoder and our
    > decoder agree with each other whether or not the order is right -- a closed loop
    > reporting green on a file VFP could not open. Until a real fixture exists, the proof
    > is a HAND-COMPUTED BYTE TABLE derived from the documentation, which a reader can
    > check against the documentation instead of against us. When a fixture arrives it is
    > added beside the byte table, and if the two disagree THE FIXTURE WINS.
- **R1b -- ANSWERED 2026-09-04 PM.** ~~one assumption remains, and no source read
  states it: that bit index 0 is the LEAST SIGNIFICANT bit of byte 0. Conventional,
  unconfirmed.~~ **Measured.** Under MSB-first numbering within the byte, row 1 of the
  R1a fixture would have read `0x40`; it reads `0x02`. Bit index 0 is the least
  significant bit of byte 0. It stays isolated in `bit_is_set`/`set_bit` regardless.
- **R1c -- ANSWERED 2026-09-05.** ~~OPEN, AND IT IS A DEFECT IN THE FIXTURE, NOT IN THE
  CODE. The R1a fixture's row 2 nulls **both** nullable fields at once, so bits 0 and 2
  are only ever observed set as a pair; exchanging them fits the file exactly as well.~~
  Two rows were **appended** to `make_nullfix.prg` (the R1a three untouched, and
  byte-identical after regeneration -- truncating the new file to three records
  reproduces the committed blob, sha256 `3c43b26e...46b34a3`). They are mirrors:

  | row | contents | predicted | measured |
  |---|---|---|---|
  | 4 | `(.NULL., "AB", "0123456789", "RR")` -- first field null only | `0x03` | **`0x03`** |
  | 5 | `(3, .NULL., "0123456789", "SS")` -- second field null only | `0x06` | **`0x06`** |

  Bit 0 is the **first** field's null bit and bit 2 the **second**'s, by measurement.
  Row 4 is the one that settles it: its ID field is blank and its VNAME field holds
  real content, so which field is null is visible in the record bytes **without
  consulting the bitmap**, and the bit that is set is bit 0.

  **WHAT THIS COST TO LEARN, and it generalizes past this lane.** Against the three-row
  fixture the R1a test *did* go red when the two null bits were exchanged -- but only
  through its own `check_eq(lay.fields[i].null_bit, N)` lines, which it had labelled
  `(INFERRED from field order)`. Those assert the implementation's belief back to
  itself. Delete exactly those two lines and the same mutation goes **green on the same
  file**: the evidence never objected, only the restatement did. A mutation-test red
  proves nothing until you know which of the two produced it. Labelling the inferred
  assertions is what made the difference visible; deleting them is what proved it.

  Mutation battery against the five-row fixture: pair order 5 red, varlength polarity
  6 red, MSB-first bit numbering 10 red, reverse field walk 5 red, **exchange the two
  null bits 6 red** (0 red on the three-row fixture once the self-referential
  assertions are removed).
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
