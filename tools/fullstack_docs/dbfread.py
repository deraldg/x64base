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
    raw_desc = []
    off = 32
    while off + 32 <= hdrlen and b[off] != 0x0D:
        raw = b[off:off + 11]
        raw_desc.append((
            raw.split(b"\0")[0].decode("latin1"),
            chr(b[off + 11]),
            b[off + 16],
            struct.unpack_from("<I", b, off + 12)[0],
        ))
        off += 32

    real: list[Field] = []
    phantoms = 0
    if any(d[3] for d in raw_desc):
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
