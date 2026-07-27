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

    real: list[Field] = []
    phantoms = 0
    off = 32
    while off + 32 <= hdrlen and b[off] != 0x0D:
        raw = b[off:off + 11]
        name = raw.split(b"\0")[0].decode("latin1")
        ftype = chr(b[off + 11])
        width = b[off + 16]
        # Rule 1: real iff the name starts with an ASCII letter.
        # NOTE the .isascii(): str.isalpha() is UNICODE-aware, so a Latin-1
        # phantom name such as 'Ë' (SYSCMD's first descriptor) passes a bare
        # .isalpha() and is admitted as a real field. That descriptor carries
        # width 250 == reclen, which then breaks reconciliation. Caught by this
        # module's own refusal on first use, which is the point of refusing.
        if name[:1].isascii() and name[:1].isalpha():
            real.append(Field(name, ftype, width))
        else:
            phantoms += 1
        off += 32

    if not real:
        raise DbfLayoutError(f"{p}: no real field descriptors found")

    # Rule 2/3: reconcile REAL widths only, or refuse.
    total = sum(f.width for f in real)
    if total + 1 != reclen:
        raise DbfLayoutError(
            f"{p}: field widths do not reconcile -- "
            f"sum(real widths)={total} +1 = {total + 1}, header reclen={reclen}, "
            f"{len(real)} real / {phantoms} phantom descriptors. "
            f"Refusing to read: a shifted parse produces plausible-looking "
            f"garbage. Check for a dropped non-alphanumeric field name."
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
            row[f.name] = rec[q:q + f.width].decode("latin1").strip()
            q += f.width
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
