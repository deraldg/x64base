#!/usr/bin/env python3
"""FIELDTYPE M5 — independent VFP DBF reader (interop gate).

This is a deliberately from-scratch, spec-based decoder for a Visual FoxPro DBF
(version 0x30/0x32). It reuses NONE of the engine's code: it parses the header,
the 32-byte field descriptors, and each record's binary fields straight from the
documented VFP on-disk layout. If it reads back the values the engine's codecs
wrote (I/B/Y/T), then those codecs are VFP-binary-compatible by an independent
reader — the M5 interop gate.

VFP binary field layouts decoded here:
  I  4-byte little-endian signed int32
  B  8-byte little-endian IEEE-754 double
  Y  8-byte little-endian signed int64, value scaled by 10^4 (currency)
  T  8 bytes = int32 Julian Day Number + int32 milliseconds since midnight
  C  fixed-width text (space padded); N/F ascii numeric; D YYYYMMDD; L logical

Usage:
  vfp_field_interop.py <table.dbf>            # dump every record's fields
  vfp_field_interop.py <table.dbf> --check    # also assert the known M5 fixture
"""

from __future__ import annotations

import struct
import sys


def jdn_to_ymd(jdn: int) -> tuple[int, int, int]:
    # Inverse of the standard Gregorian->JDN used by the codec (Fliegel/Van Flandern).
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return year, month, day


def decode_field(kind: str, raw: bytes):
    if kind == "C":
        return raw.decode("latin-1").rstrip(" \x00")
    if kind in ("N", "F"):
        s = raw.decode("latin-1").strip()
        return s
    if kind == "D":
        return raw.decode("latin-1").strip()
    if kind == "L":
        return raw.decode("latin-1").strip()
    if kind == "I":
        return struct.unpack("<i", raw[:4])[0]
    if kind == "B":
        return struct.unpack("<d", raw[:8])[0]
    if kind == "Y":
        return struct.unpack("<q", raw[:8])[0] / 10000.0
    if kind == "T":
        jdn, ms = struct.unpack("<ii", raw[:8])
        if jdn == 0 and ms == 0:
            return None
        y, mo, dy = jdn_to_ymd(jdn)
        sec = ms // 1000
        hh, mi, ss = sec // 3600, (sec % 3600) // 60, sec % 60
        return f"{y:04d}{mo:02d}{dy:02d}{hh:02d}{mi:02d}{ss:02d}"
    # X (pronoun) and any custom/binary type: show raw hex so the reader stays honest.
    return "0x" + raw.hex()


def read_dbf(path: str):
    with open(path, "rb") as fh:
        data = fh.read()

    version = data[0]
    n_records, header_len, record_len = struct.unpack_from("<IHH", data, 4)

    fields = []
    off = 32
    while data[off] != 0x0D:  # 0x0D terminates the descriptor array
        desc = data[off:off + 32]
        name = desc[0:11].split(b"\x00", 1)[0].decode("latin-1")
        ftype = chr(desc[11])
        flen = desc[16]
        fdec = desc[17]
        fields.append((name, ftype, flen, fdec))
        off += 32

    records = []
    for r in range(n_records):
        base = header_len + r * record_len
        row = data[base:base + record_len]
        deleted = row[0:1] == b"*"
        pos = 1
        values = {}
        for name, ftype, flen, fdec in fields:
            values[name] = decode_field(ftype, row[pos:pos + flen])
            pos += flen
        records.append((deleted, values))

    return version, fields, records


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    do_check = "--check" in sys.argv[2:]

    version, fields, records = read_dbf(path)
    print(f"file        : {path}")
    print(f"version byte : 0x{version:02X}  "
          f"({'VFP' if version in (0x30, 0x31, 0x32) else 'NON-VFP'})")
    print("fields       : " + ", ".join(f"{n} {t}({l})" for n, t, l, d in fields))
    print(f"records      : {len(records)}")
    for i, (deleted, vals) in enumerate(records, 1):
        flag = " [deleted]" if deleted else ""
        print(f"  rec {i}{flag}: " +
              ", ".join(f"{n}={vals[n]!r}" for n, _, _, _ in fields))

    if not do_check:
        return 0

    # Known M5 fixture written by vfp_types_make.dts.
    expected = [
        {"NAME": "Ada",   "NUM": 50000000,    "AMT": 3.140625,
         "BAL": 1234.5678, "TS": "20000101120000"},
        {"NAME": "Grace", "NUM": -2147483648, "AMT": -0.5,
         "BAL": -99.9999,  "TS": "19700101000000"},
    ]
    failures = 0
    for i, exp in enumerate(expected):
        got = records[i][1]
        for key, want in exp.items():
            have = got.get(key)
            ok = (abs(have - want) < 1e-9) if isinstance(want, float) else (have == want)
            if not ok:
                failures += 1
                print(f"  MISMATCH rec {i+1} {key}: got {have!r} want {want!r}")
    if failures:
        print(f"FAIL: {failures} field mismatch(es) — codecs are NOT VFP-compatible")
        return 1
    print("PASS: independent VFP reader decoded every I/B/Y/T value the engine wrote")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
