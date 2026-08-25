# AIF-127 -- an x64 table with thirteen rows is unreadable, and fourteen reads fine

    Run    : COWORK-20260824-001 (member.ai.claude.cowork), for member.derald
    Claim  : coordination/aif/AIF-127.claim
    Found  : 2026-08-25, opening the manualgen MAN* catalog for flush v5 Phase 6
    Tier   : SOURCE-EVIDENCED at file:line, and the affected file proven INTACT
             by arithmetic.
    Status : **review-needed. NOT FIXED.** Read-only throughout. The reader
             belongs to the doc-tooling lane and the fix is a design call.

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

## Good Neighbor note

    WHAT CHANGED   : this finding and coordination/aif/AIF-127.claim. No source,
                     no data, no reader, no catalog. Nothing was fixed.
    WHOSE AREA     : tools/fullstack_docs/dbfread.py belongs to the doc-tooling
                     lane, owner member.derald. READ ONLY here.
    AUTHORIZATION  : the owner's instruction to tidy up and run through
                     manualgen; found while opening the MAN* catalog for
                     Phase 6. AIF-127 allocated by tools/coordination/next_aif.py.
    VERIFY OR UNDO : re-derives from the file itself --
                       13 x 317 + 431 = 4552 against a 4553-byte file, and
                       byte 32 of MANHASH.dbf is 0x0D while X64M sits at 257.
                     Undo is deleting the two files.
