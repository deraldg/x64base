# AIF-127 -- an x64 table with thirteen rows is unreadable, and fourteen reads fine

    Run    : COWORK-20260824-001 (member.ai.claude.cowork), for member.derald
    Claim  : coordination/aif/AIF-127.claim
    Found  : 2026-08-25, opening the manualgen MAN* catalog for flush v5 Phase 6
    Tier   : SOURCE-EVIDENCED at file:line, and the affected file proven INTACT
             by arithmetic.
    Status : **FIXED 2026-08-25, review-needed.** Option 3 of section 5 --
             positive identification plus validation. See section 8.

---

## 1. The finding

`docs/manuals/developer/manualgen/accepted_catalogs/man_catalog_v1/dbf/MANHASH.dbf`
cannot be read by `tools/fullstack_docs/dbfread.py`, the project's own shared
X64/DBF reader. It fails with `no real field descriptors found`.

**The file is not damaged.** Proven without parsing a single field:

    13 rows x 317 reclen + 431 hdrlen = 4,552
    file size                         = 4,553   (+1 for the EOF marker)

Thirteen complete records, exactly where the header says they are.

**It is unreadable because it has thirteen rows.** Give it fourteen and it
reads.

## 2. The mechanism

An x64 DBF opens a phantom block at offset 32 whose first field is the row
count. `dbfread.py:175` locates the classic descriptor terminator like this:

    term = 32
    while term + 32 <= hdrlen and b[term] != 0x0D:
        term += 32
    ext = b[term + 1:hdrlen] if term < hdrlen else b""
    if ext[:4] == b"X64M":

**The scan starts INSIDE the phantom block, and 13 == 0x0D.** So `b[32]` is the
terminator byte on the very first probe, `term` stays at 32, `ext` begins at 33,
and the `X64M` marker -- which is at offset **257** in every MAN table -- is
never found. The classic path at `:113` uses the same test and stops in the same
place, yielding zero descriptors.

Measured across the accepted catalog, byte 32 IS the low byte of the row count
in every table:

    MANRUN      nrec=3    byte32=0x03    X64M at 257   ok
    MANREVIEW   nrec=3    byte32=0x03    X64M at 257   ok
    MANPUB      nrec=4    byte32=0x04    X64M at 257   ok
    MANAPPX     nrec=6    byte32=0x06    X64M at 257   ok
    MANMEDIA    nrec=9    byte32=0x09    X64M at 257   ok
    MANANCHOR   nrec=9    byte32=0x09    X64M at 257   ok
    MANSECTION  nrec=25   byte32=0x19    X64M at 289   ok
    MANHASH     nrec=13   byte32=0x0d    X64M at 257   UNREADABLE

## 3. Why this class matters more than one table

**The failure is DATA-DEPENDENT and periodic.** Any x64 table whose row count
has `0x0D` in its low byte is affected: **13, 269, 525, 781, ...** -- every 256
rows. A table that reads correctly today becomes unreadable when it grows to the
wrong size, and readable again one row later. Nothing about the schema, the
writer or the file changes.

**It is silent in the worst way.** The reader does not return partial data or a
wrong value; it declines. That is the RIGHT behaviour and it is why this is a
bug report rather than a data-loss report. But the caller sees "this table has
no fields", which reads as a malformed file rather than a reader limitation, and
the natural next move is to suspect the data.

**The affected table is the integrity table.** `MANHASH` is where the manualgen
catalog records the hashes it verifies its own published artifacts against. The
one MAN table the doc tooling cannot open is the one that proves the others are
what they claim to be.

## 4. The reader was RIGHT to derive, and its own comment says why

`dbfread.py:170-174` explains that it deliberately does not key on the block
version number:

> Keying on the version number would have hardcoded an assumption that a v3
> could quietly break.

That instinct is correct and should be kept. The defect is not the choice to
derive -- it is that this particular derivation reads one byte at a fixed offset
whose value is CONTENT, not structure. A terminator is a structural fact; the
low byte of a row count is data that can impersonate it.

## 5. Options, not a ruling

1. **Find `X64M` by search, not by scan.** The four-byte marker is unambiguous
   and already located at a known offset in practice. Search the header span for
   it before trusting any terminator.
2. **Validate the candidate terminator.** A terminator at offset 32 means a
   table with zero fields, which no real table has. Requiring at least one
   plausible descriptor -- or that `X64M` follows -- rejects the false positive
   without hardcoding a version.
3. **Both.** (1) is the positive identification; (2) is the sanity check that
   makes a future surprise loud instead of empty.

Whichever is chosen, **the regression test writes itself: a 13-row x64 table.**
There is one on disk already.

## 6. What is NOT claimed

- That any data was lost. It was not; section 1 proves the file is complete.
- That `help_store_check.py` shares the bug. It does not reach this code -- it
  refuses non-0x03 formats outright (that guard was added the same day, for the
  same underlying reason: a reader should decline what it cannot read).
- That the X64M block layout is fully understood by this steward. It is not.
  `dbfread.py` reads the other seven tables correctly and is the authority.
- Any measurement of how many x64 tables tree-wide currently sit at an affected
  row count. Not surveyed.

---

## 7. WHAT THE BLOCKED READ WAS HIDING -- added 2026-08-25, same day

Section 3 argued this class matters because the affected table is the integrity
table. That was an argument. **It is now a measurement.**

MANHASH was opened with a one-off parser that locates `X64M` positively rather
than deriving it from the `0x0D` terminator, and every one of its thirteen
declared artifacts was re-hashed against disk:

    match 12   drift 1   missing 0

The one drifted row is **MANHASH-001, the published developer manual** -- the
only artifact in the catalog that anyone reads:

    accepted   5C45339E6DF0406913092991E85A37FAD77A03B5C241E0C53EB5DB89543F923A
    on disk    5ADFCDED44B4C7F4B0938EAC526FA466A5C4BB48FD59BFC85DA582E91E7F2C53

    catalog promoted     2026-05-27 14:47:38Z
    publication written  2026-05-27 19:13:55Z   (4h 26m later, same day)

and `man_catalog_v1_manifest.json` records `"publication_replacement": 0`, so
the promotion did not do it.

**The catalog has been asserting a stale hash for its headline artifact for
ninety days, and the assertion lives in the one table the reader declines to
open.** This is not a coincidence in the bad sense -- MANHASH is the integrity
table precisely because it is the one that changes when artifacts change, so it
is the table most likely to sit at an arbitrary row count. But it does raise the
priority: the defect is not "one table is awkward to read", it is **"the drift
detector is the thing that is unreadable."**

This does NOT change what is claimed in section 6. No data was lost; the drift
is an addition, not damage; the reader is still right to decline rather than
guess. The one-off parser was not committed and nothing here fixes AIF-127.

Full verification pass:
`docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260812-001/manualgen_phase/PHASE6_CATALOG_VERIFICATION_V1.md`

---

## 8. FIXED 2026-08-25 -- option 3, and proven on 206 files

Section 5 offered three options and recommended neither. **Option 3 was taken:
identify positively AND validate**, because (1) is the identification and (2) is
what makes a future surprise loud instead of empty.

### 8a. The change

One helper, `_descriptor_end(b, hdrlen) -> (desc_end, ext_off)`, now answers
both questions the old code answered twice with the same flawed scan -- the
classic descriptor walk at `:113` and the X64M locate at `:175`. Both call it.

    x = b.find(b"X64M", 32, hdrlen)
    if x > 32 and b[x - 1] == 0x0D and (x - 1 - 32) % 32 == 0:
        return x - 1, x
    ... classic scan ...
    if off == 32:  raise DbfLayoutError(...)

**What was kept.** The module's refusal to key on the block version number
survives untouched -- "keying on the version number would have hardcoded an
assumption that a v3 could quietly break" was right and is still right. The
defect was never the choice to derive; it was deriving from **one byte at a
fixed offset whose value is CONTENT, not structure.**

**The validation is not decoration.** The marker is accepted only when the byte
before it really is `0x0D` and the descriptor array divides evenly into 32-byte
records from offset 32. Measured across every x64 table in the tree -- both
accepted MAN catalogs and the eight SYS* authorities -- **that invariant holds
21 of 21**, at marker offsets from 225 to 769.

**A terminator on the first probe now RAISES** instead of yielding an empty
descriptor list. It describes a table with zero fields, which no real table has.

### 8b. Proven -- 206 files, old reader against new

    files tested   206      (MAN catalogs, metadata authorities, HELP store,
                             and every fixture under dottalkpp/data/dbf)
    identical      205
    FIXED            1      MANHASH.dbf -- 5 fields, 13 rows
    BROKE            0
    differ           0
    error-both       0

Signatures compared were field count, field names, types, widths, declared row
count and live row count. **Nothing changed except the file that could not be
read.**

MANHASH now verifies through the SHARED reader, with no one-off parser, and
reproduces the earlier hand-rolled result exactly: **match 12, drift 1, missing
0**, the drift being MANHASH-001. The workaround described in
`PHASE6_CATALOG_VERIFICATION_V1.md` section 4 is no longer needed.

### 8c. The guard shown to fail before being trusted

Section 5 said "the regression test writes itself: a 13-row x64 table." It does,
and the periodicity claim of section 3 is now demonstrated end to end rather
than argued. A real table (MANANCHOR) re-stamped to each row count, padded, and
read by both readers:

    nrec=12    byte32=0x0c   OLD reads          NEW reads
    nrec=13    byte32=0x0d   OLD FAILS          NEW reads
    nrec=269   byte32=0x0d   OLD FAILS          NEW reads
    nrec=270   byte32=0x0e   OLD reads          NEW reads
    nrec=525   byte32=0x0d   OLD FAILS          NEW reads

13, 269, 525 -- exactly the predicted sequence, failing before and reading
after, with the neighbours 12, 270 unaffected in both.

### 8d. A correction to section 2, found while building that fixture

Section 2 says "an x64 DBF opens a phantom block at offset 32 whose first field
is the row count", and section 3 says byte 32 IS the low byte of the row count.
**More precisely: the phantom block carries its OWN u32 row count at offset 32,
independent of the header's at offset 4.**

The first attempt at the fixture above re-stamped only the header count and byte
32 stayed at its original `0x09` -- the table read fine and proved nothing. Both
had to be set.

Measured: **in all 21 x64 tables the phantom count equals the header count.**
That is a fact about how they were written, not a guarantee. A writer that
updated one and not the other would produce a table stating its row count twice,
differently -- which nothing currently checks. **Recorded, not pursued.**

### 8e. Not fixed, and deliberately not touched

`dbfread.py:296-300` carries TWO consecutive `if not real: raise` guards with
different messages. The second is unreachable. It is pre-existing, it is
harmless, and widening a targeted fix to tidy adjacent code is how a clean diff
becomes an unreviewable one. **Left alone on purpose.**

---

## Good Neighbor note

    WHAT CHANGED   : 2026-08-24 -- this finding and coordination/aif/AIF-127.claim.
                     2026-08-25 -- tools/fullstack_docs/dbfread.py, one helper
                     added and two scans replaced by calls to it, plus sections
                     7 and 8 here. No data, no catalog, no publication.
    WHOSE AREA     : tools/fullstack_docs/dbfread.py belongs to the doc-tooling
                     lane, owner member.derald. READ ONLY here.
    AUTHORIZATION  : the owner's instruction to tidy up and run through
                     manualgen; found while opening the MAN* catalog for
                     Phase 6. AIF-127 allocated by tools/coordination/next_aif.py.
    VERIFY OR UNDO : re-derives from the file itself --
                       13 x 317 + 431 = 4552 against a 4553-byte file, and
                       byte 32 of MANHASH.dbf is 0x0D while X64M sits at 257.
                     Undo is deleting the two files.
