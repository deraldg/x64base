#!/usr/bin/env python3
"""
Shared X64/DBF reader for the full-stack documentation tooling.

WHY THIS FILE EXISTS
    The same parsing mistake has now been made three times in this run, by the
    same author, each time in a fresh throwaway script:

      1. help_guard_v1  -- an `[A-Z0-9_]+` field-name filter silently dropped the
         unique-name fallback field `LOCALIZE~1`, shifting every subsequent field
         by 24 bytes. sha256("AREA") then appeared to match SOURCE_HASH, which
         would have been reported as "SOURCE_HASH is just the title hash". False.

      2. SYSSUBCMD probe -- phantoms excluded correctly, but by luck.

      3. SYSCMD probe -- summed ALL descriptors including phantoms, so
         reconciliation failed; the extraction loop then walked a 250-byte
         phantom across the whole 250-byte record and reported TYPE, VIS and
         ACTIVE as empty for all 203 rows. They are not: TYPE='command',
         VIS='public'. That would have been filed as "SYSCMD is unpopulated".

    Three near-misses, all of which would have produced a confident, wrong,
    documented finding. The defect is not carelessness, it is that the parse
    was re-derived each time. One reader, used everywhere, or it happens again.

THE X64 (0x64) EXTENDED HEADER
    An X64 DBF prefixes the ordinary field descriptors with PHANTOM descriptors
    whose 11-byte name field is NOT a printable identifier. The first phantom's
    width byte commonly holds the RECORD LENGTH, which is what makes a naive
    sum look plausible while being wrong.

    Rules, in this order and no other:
      1. A descriptor is REAL iff its name begins with an ASCII letter.
         Not `isidentifier()`, not `[A-Z0-9_]+` -- the unique-name fallback
         emits `LOCALIZE~1` when two logical names truncate to the same 10
         physical characters, and `~` and digits are legitimate.
      2. Reconcile REAL widths only: sum(widths) + 1 == reclen.
         The +1 is the leading deleted-flag byte.
      3. If it does not reconcile, RAISE. Never guess at a layout you cannot
         verify -- a shifted read is worse than no read, because it looks like
         data.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


class DbfLayoutError(RuntimeError):
    """Field widths do not reconcile against the header's record length."""


@dataclass(frozen=True)
class Field:
    name: str
    type: str
    width: int
    displacement: int = 0      # bytes 12-15 of the descriptor, as DECLARED
    offset: int = 0            # what this reader computed by accumulation


@dataclass(frozen=True)
class Table:
    path: Path
    header_rows: int          # row count as declared by the header
    reclen: int
    fields: tuple[Field, ...]
    rows: tuple[dict[str, str], ...]   # undeleted rows only
    deleted: int
    phantoms: int

    @property
    def live(self) -> int:
        return len(self.rows)


def _descriptor_end(b: bytes, hdrlen: int) -> tuple[int, int]:
    """Return (desc_end, ext_off): where the classic 32-byte descriptor array
    stops, and where the X64M extension begins (hdrlen when there is none).

    AIF-127. This exists because the old derivation read ONE BYTE AT A FIXED
    OFFSET WHOSE VALUE IS CONTENT, NOT STRUCTURE. An x64 file opens a phantom
    block at offset 32 whose first field is the row count, and the scan for the
    0x0D descriptor terminator started there:

        term = 32
        while term + 32 <= hdrlen and b[term] != 0x0D:
            term += 32

    13 == 0x0D. So MANHASH.dbf -- thirteen rows, file proven intact by
    arithmetic -- terminated on the very first probe, X64M at offset 257 was
    never found, and the reader declined a perfectly good table. The failure is
    DATA-DEPENDENT and PERIODIC: any x64 table whose row count carries 0x0D in
    its low byte is affected -- 13, 269, 525, 781, every 256 rows -- so a table
    reads today, becomes unreadable when it grows, and reads again one row
    later, with no change to schema, writer or file.

    KEEPING WHAT WAS RIGHT. The module deliberately does not key on the block
    version number ("keying on the version number would have hardcoded an
    assumption that a v3 could quietly break"), and that instinct is kept. A
    terminator is a STRUCTURAL fact; the low byte of a row count is data that
    can impersonate one. So:

      1. IDENTIFY POSITIVELY. Search the header span for the unambiguous four
         byte X64M marker before trusting any terminator.
      2. VALIDATE THE CANDIDATE. Accept the marker only when the byte before it
         really is 0x0D and the descriptor array divides evenly into 32-byte
         records from offset 32. Measured across all 21 x64 tables in this tree
         -- both accepted MAN catalogs and the eight SYS* authorities -- that
         invariant holds 21 of 21, at marker offsets from 225 to 769.
      3. REFUSE THE IMPOSSIBLE. A terminator on the first probe describes a
         table with ZERO fields, which no real table has. Raise instead of
         returning an empty descriptor list, so a future surprise is loud
         rather than empty.
    """
    x = b.find(b"X64M", 32, hdrlen)
    if x > 32 and b[x - 1] == 0x0D and (x - 1 - 32) % 32 == 0:
        return x - 1, x

    off = 32
    while off + 32 <= hdrlen and b[off] != 0x0D:
        off += 32

    if off == 32:
        if x >= 0:
            raise DbfLayoutError(
                f"X64M found at offset {x} but the descriptor array does not "
                f"reconcile (byte {x - 1} is 0x{b[x - 1]:02x}, expected 0x0d; "
                f"span {x - 1 - 32} is not a multiple of 32). This layout is "
                "not the one this reader understands -- refusing rather than "
                "guessing at a shifted read."
            )
        raise DbfLayoutError(
            "descriptor terminator found at offset 32, which describes a table "
            "with ZERO fields. No real table has none, so this is a false "
            "terminator (AIF-127) or a malformed header -- refusing rather "
            "than returning an empty field list."
        )
    return off, hdrlen


def read(path: str | Path, *, include_deleted: bool = False) -> Table:
    p = Path(path)
    b = p.read_bytes()
    if len(b) < 32:
        raise DbfLayoutError(f"{p}: too small to be a DBF ({len(b)} bytes)")

    nrows, hdrlen, reclen = struct.unpack_from("<IHH", b, 4)

    # ----------------------------------------------------------------- #
    # Descriptor classification
    # ----------------------------------------------------------------- #
    # PRIMARY RULE: DISPLACEMENT CONTIGUITY.
    #
    # Bytes 12-15 of each descriptor declare the field's byte offset within the
    # record. Real fields declare contiguous offsets starting at 1 (byte 0 is
    # the deleted flag); X64 phantoms declare 0. So the file states which
    # descriptors are fields, and the reader can simply agree with it.
    #
    # WHY THIS REPLACED THE NAME HEURISTIC. The old rule was "real iff the name
    # begins with an ASCII letter", which is a guess about bytes that are not
    # names at all. It failed on SYSFUNC, whose first phantom is named 0x45 --
    # the letter 'E'. That admitted a spurious 10-byte field and shifted every
    # real field by 10; the width-sum check caught the total (788 vs 778) but
    # could not say WHERE. The displacements said exactly where: FUNC_ID
    # declared 1 while the reader computed 11, and so on, uniformly, for all 21
    # fields. SYSFUNC was unreadable by this module until the file was allowed
    # to answer the question itself.
    #
    # FALLBACK: writers that leave displacement zero throughout get the old
    # name heuristic, so older tables still read. That path keeps its ASCII
    # caveat -- str.isalpha() is Unicode-aware, and SYSCMD's phantom 'Ë' passes
    # a bare .isalpha().
    desc_end, ext_off = _descriptor_end(b, hdrlen)

    raw_desc = []
    off = 32
    while off + 32 <= desc_end:
        raw = b[off:off + 11]
        raw_desc.append((
            raw.split(b"\0")[0].decode("latin1"),
            chr(b[off + 11]),
            b[off + 16],
            struct.unpack_from("<I", b, off + 12)[0],
        ))
        off += 32

    # ----------------------------------------------------------------- #
    # X64M extended header -- the AUTHORITATIVE field table when present
    # ----------------------------------------------------------------- #
    # After the 0x0D descriptor terminator, X64 writes a block:
    #
    #   +0   "X64M"
    #   +4   u32  version (2 observed)
    #   +8   u32  extension length
    #   +12  u32  reserved (0 observed)
    #   +16  u32  table-name length
    #   +20  u32  field-record offset (44 observed)
    #   +24  u32  field count
    #   +28  u32  names-blob offset
    #   +32  u32  names-blob length
    #   +36..44   two u32s, purpose not identified -- recorded as unknown
    #             rather than guessed
    #   +44  field records, 16 bytes each:
    #             u32 index, u32 name offset, u32 name length, u32 WIDTH
    #   names blob: table name, then each field name, concatenated
    #
    # TWO THINGS LIVE HERE THAT THE CLASSIC DESCRIPTOR CANNOT HOLD:
    #
    #   TRUE WIDTH, 32-bit. The classic width byte is CLAMPED to 0xFF. That is
    #   why comments/MEMO_LINES.dbf was unreadable: LINECONT is C(1024) and read
    #   back as 255, leaving 769 bytes of every record undescribed. Nothing was
    #   corrupt; the reader simply could not express the field.
    #
    #   LOGICAL NAME, up to 128 chars. The classic name is 10 bytes, so
    #   HELP_TOPIC_LOCALE's TOPIC_LOCALE_ID (15 chars) is truncated there, and
    #   collisions get the unique-name fallback that produced LOCALIZE~1 -- the
    #   value that broke an earlier field filter and nearly produced a false
    #   SOURCE_HASH finding.
    #
    # Verified against three tables of different shape (3, 14 and 20 fields;
    # one field wider than 255): sum(X64M widths) + 1 == reclen in every case.
    # TWO VERSIONS EXIST, and the block states which without being asked:
    #
    #   v2  16-byte records: idx, name-offset, name-length, WIDTH
    #   v1  12-byte records: idx, name-offset, name-length      (no width)
    #
    # v1 carries logical NAMES only; widths still come from the classic
    # descriptor byte. Rather than branch on the version field, DERIVE the
    # stride from the block's own geometry:
    #
    #     stride = (names_off - frec_off) / nfields
    #
    # which is self-checking: if it does not divide evenly, the block is not
    # laid out the way this reader believes and it declines the extension
    # instead of reading past the field table. Keying on the version number
    # would have hardcoded an assumption that a v3 could quietly break.
    x64m: list[tuple[str, int | None]] = []
    ext = b[ext_off:hdrlen] if ext_off < hdrlen else b""
    if ext[:4] == b"X64M":
        try:
            (_ver, _extlen, _rsv, _tnamelen, frec_off,
             nfields, names_off, names_len) = struct.unpack_from("<8I", ext, 4)
            span = names_off - frec_off
            if nfields > 0 and span > 0 and span % nfields == 0:
                stride = span // nfields
                blob = ext[names_off:names_off + names_len]
                for i in range(nfields):
                    base = frec_off + stride * i
                    # The stored index is 1-BASED (house convention: 0-based
                    # behind the scenes, 1-based at user fronts -- and a field
                    # number is a user front). It is read but NOT used: fields
                    # are taken in FILE ORDER, so a sparse or renumbered index
                    # cannot silently reorder a record layout. An earlier draft
                    # keyed a dict on it and raised KeyError(2) on four tables.
                    _idx, noff, nlen = struct.unpack_from("<3I", ext, base)
                    width = (struct.unpack_from("<I", ext, base + 12)[0]
                             if stride >= 16 else None)
                    x64m.append((blob[noff:noff + nlen].decode("latin1"), width))
        except (struct.error, IndexError):
            x64m = []          # malformed extension: fall through, do not guess

    real: list[Field] = []
    phantoms = 0
    if x64m:
        # X64M supplies logical name and (v2) true width. The classic
        # descriptors still supply the TYPE character and, for v1, the width --
        # so pair them in file order across the non-phantom descriptors.
        classic = [d for d in raw_desc if d[3]] or raw_desc[-len(x64m):]
        run = 1
        for i, (name, width) in enumerate(x64m):
            ftype = classic[i][1] if i < len(classic) else "C"
            w = width if width is not None else (classic[i][2] if i < len(classic) else 0)
            real.append(Field(name, ftype, w, run, run))
            run += w
        phantoms = len(raw_desc) - len(x64m)
    elif any(d[3] for d in raw_desc):
        run = 1
        for name, ftype, width, disp in raw_desc:
            if disp == run:
                real.append(Field(name, ftype, width, disp, run))
                run += width
            else:
                phantoms += 1
    else:
        run = 1
        for name, ftype, width, disp in raw_desc:
            if name[:1].isascii() and name[:1].isalpha():
                real.append(Field(name, ftype, width, disp, run))
                run += width
            else:
                phantoms += 1

    if not real:
        raise DbfLayoutError(f"{p}: no real field descriptors found")

    if not real:
        raise DbfLayoutError(f"{p}: no field descriptors could be classified")

    # Final agreement: the last field must end exactly at the record length.
    # With displacement classification this is a genuine second opinion rather
    # than a restatement -- offsets came from the file, this total comes from
    # the widths.
    if run != reclen:
        raise DbfLayoutError(
            f"{p}: fields end at {run} but header reclen={reclen} "
            f"({len(real)} real / {phantoms} phantom descriptors). "
            f"Refusing to read."
        )

    rows: list[dict[str, str]] = []
    deleted = 0
    for r in range(nrows):
        o = hdrlen + r * reclen
        rec = b[o:o + reclen]
        if len(rec) < reclen:
            break                     # truncated tail; stop rather than pad
        is_del = rec[:1] == b"*"
        if is_del:
            deleted += 1
            if not include_deleted:
                continue
        q = 1
        row: dict[str, str] = {}
        for f in real:
            raw = rec[q:q + f.width].decode("latin1").strip()
            q += f.width
            if f.type == "M":
                # MEMO FIELDS ARE NOT RESOLVED. The record holds a POINTER to a
                # block in the sidecar memo file; this reader does not follow it.
                # Returning the raw pointer bytes as if they were text is how a
                # 300-character summary reads back as "&" and gets mistaken for
                # an empty or corrupted field -- which happened on first use,
                # while checking whether a reseed had landed.
                #
                # So the value is REPLACED with an explicit marker rather than
                # returned. A caller that needs memo CONTENT must read the
                # sidecar; a caller comparing non-memo columns is unaffected and
                # can no longer silently compare pointers.
                row[f.name] = f"<memo:unresolved ptr={raw!r}>" if raw else ""
            else:
                row[f.name] = raw
        if include_deleted:
            row["_deleted"] = "T" if is_del else "F"
        rows.append(row)

    return Table(
        path=p,
        header_rows=nrows,
        reclen=reclen,
        fields=tuple(real),
        rows=tuple(rows),
        deleted=deleted,
        phantoms=phantoms,
    )


def main() -> int:
    import argparse
    import collections

    ap = argparse.ArgumentParser(description="Dump or profile an X64/DBF table.")
    ap.add_argument("path")
    ap.add_argument("--rows", type=int, default=0, help="print first N rows")
    ap.add_argument("--distinct", action="append", default=[],
                    help="report the value distribution of a column (repeatable)")
    a = ap.parse_args()

    t = read(a.path)
    print(f"{t.path.name}: {t.live} live / {t.deleted} deleted / "
          f"{t.header_rows} declared, reclen={t.reclen}, "
          f"{len(t.fields)} real + {t.phantoms} phantom fields")
    print("  " + ", ".join(f"{f.name}:{f.type}{f.width}" for f in t.fields))

    for col in a.distinct:
        c = collections.Counter(r.get(col, "<no such column>") for r in t.rows)
        print(f"\n{col}:")
        for v, k in c.most_common(20):
            print(f"  {k:6}  {v!r}")

    for r in t.rows[: a.rows]:
        print()
        for f in t.fields:
            if r[f.name]:
                print(f"  {f.name:12} {r[f.name][:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
