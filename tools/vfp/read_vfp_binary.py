#!/usr/bin/env python3
"""Read the DBF-shaped VFP binaries: .DBF .SCX .VCX .FRX .MNX .LBX.

Owner: member.derald. Author: member.ai.claude.cowork. Lane: AIF-120. 2026-08-18.
Python 3 stdlib only, per AIF-085.

All six of these formats are the same thing: a DBF table, optionally with a memo
sidecar under a different extension. A form is a table of objects, a menu is a
table of menu lines, a report is a table of bands. So one reader covers them and
the only per-format knowledge is which extension holds the memos and which
columns mean something.

Modes:
  struct   field layout, house STRUCT order (default)
  rows     every record, memos resolved
  form     .SCX / .VCX: object tree from PARENT (a dotted path), plus the
           implicit children that count properties create but no record describes
  menu     .MNX: menu tree from LEVELNAME + ITEMNUM, with NUMITEMS verified

`form` and `menu` are not interchangeable and each refuses the other's format by
naming the columns it did not find. The three designer formats share a container
and nothing else: .SCX parents by name or dotted path, .MNX by LEVELNAME
ordinal, and neither convention predicts the other.

Absence is reported as a measurement, not as silence. `struct` prints memo
occupancy counts, so "METHODS is empty" is distinguishable from "this reader
could not see METHODS" -- the failure that a memo reader with a wrong block size
produces, and which looks exactly like a form with no code.
"""

import os
import struct
import sys

MEMO_EXT = {
    ".dbf": ".fpt", ".scx": ".sct", ".vcx": ".vct",
    ".frx": ".frt", ".mnx": ".mnt", ".lbx": ".lbt",
}

# Object-table columns, shared by .SCX and .VCX.
FORM_COLS = ("PLATFORM", "OBJNAME", "PARENT", "BASECLASS", "CLASS",
             "CLASSLOC", "PROPERTIES", "METHODS", "OBJCODE")


# VFP's language-driver byte (DBF header offset 29) -> a Python codec.
# AIF-120 R33. The reader decoded every byte as latin1 and never looked at this
# byte, which is correct for exactly one of the seventeen values below and silently
# wrong for the rest. x64base's own message catalog already ships five locales
# behind SET LOCALE, so this is the design table failing a standard the rest of the
# tree already meets.
LANGUAGE_DRIVER = {
    0x00: None,          0x01: "cp437",   0x02: "cp850",   0x03: "cp1252",
    0x64: "cp852",       0x65: "cp866",   0x66: "cp865",   0x67: "cp861",
    0x78: "cp950",       0x79: "cp949",   0x7a: "cp936",   0x7b: "cp932",
    0x7c: "cp874",       0x7d: "cp1255",  0x7e: "cp1256",
    0xc8: "cp1250",      0xc9: "cp1251",  0xca: "cp1254",  0xcb: "cp1253",
}
FALLBACK_ENCODING = "latin1"     # byte-preserving; never raises, never correct


class Dbf:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as fh:
            self.d = fh.read()
        d = self.d
        if len(d) < 32:
            raise ValueError("%s: too short to be a DBF (%d bytes)" % (path, len(d)))
        self.version = d[0]
        self.codepage_byte = d[29]
        self.encoding = LANGUAGE_DRIVER.get(d[29]) or FALLBACK_ENCODING
        self.encoding_declared = LANGUAGE_DRIVER.get(d[29]) is not None
        self.nrec, = struct.unpack("<I", d[4:8])
        self.hlen, = struct.unpack("<H", d[8:10])
        self.rlen, = struct.unpack("<H", d[10:12])

        self.fields = []            # (name, type, width, decimals)
        off = 32
        while off < len(d) and d[off] not in (0x0D, 0x00):
            fb = d[off:off + 32]
            if len(fb) < 32:
                break
            self.fields.append((fb[:11].split(b"\0")[0].decode("ascii", "replace"),
                                chr(fb[11]), fb[16], fb[17]))
            off += 32

        # Width arithmetic is a cheap integrity check: the field widths plus the
        # one-byte deletion flag must equal the record length. When it does not,
        # the header was misread and every row after would be silently skewed.
        self.width_sum = 1 + sum(f[2] for f in self.fields)
        self.width_ok = (self.width_sum == self.rlen)

        self.undecodable = set()
        self._cur = None
        self.memo = None
        self.blocksize = 0
        self.memo_path = None
        stem, ext = os.path.splitext(path)
        want = MEMO_EXT.get(ext.lower())
        if want:
            for cand in (stem + want, stem + want.upper()):
                if os.path.exists(cand):
                    with open(cand, "rb") as fh:
                        self.memo = fh.read()
                    self.memo_path = cand
                    self.blocksize, = struct.unpack(">H", self.memo[6:8])
                    break

    def _dec(self, raw, field=None):
        """Decode using the codepage the FILE declares, not the one we assume.

        Falling back matters and so does knowing WHERE. A `.SCX` keeps compiled
        method bytecode in `OBJCODE` and binary in the `RESERVED*` columns; those
        are not text in any codepage and must not be reported as an encoding
        problem. A `PROPERTIES` or `OBJNAME` that will not decode is a real one.
        """
        try:
            return raw.decode(self.encoding)
        except (UnicodeDecodeError, LookupError):
            if field:
                self.undecodable.add(field)
            return raw.decode(FALLBACK_ENCODING)

    def _binary_value(self, typ, raw):
        """VFP's BINARY column types. R33.3.

        `I`, `Y`, `B`, `T`, `W` and `0` hold packed bytes, not text, and this
        reader decoded every non-memo column as characters. Measured: 79 such
        columns across the corpus -- 46 `I`, 20 `Y`, 3 `B`, plus `T`, `W` and the
        `0` null-flags column. Nothing this lane has measured used one, because
        STUDENTS and ACCOUNTS declare `N` and `C` throughout; checked, not assumed.
        """
        try:
            if typ == "I":
                return struct.unpack("<i", raw[:4])[0]
            if typ == "Y":                    # currency: int64 scaled by 10^4
                return struct.unpack("<q", raw[:8])[0] / 10000.0
            if typ == "B":
                return struct.unpack("<d", raw[:8])[0]
            if typ == "T":                    # datetime: Julian day + ms past midnight
                jd, ms = struct.unpack("<ii", raw[:8])
                return "%d:%d" % (jd, ms)
        except struct.error:
            pass
        return raw                            # `W`, `G`, `0`: hand back the bytes

    BINARY_TYPES = frozenset("IYBTW0G")

    # Columns that are binary by design, so a decode failure in them says nothing.
    BINARY_FIELDS = frozenset((
        "OBJCODE", "OLE", "OLE2", "USER", "PROTECTED",
        "RESERVED1", "RESERVED2", "RESERVED3", "RESERVED4",
        "RESERVED5", "RESERVED6", "RESERVED7", "RESERVED8",
    ))

    @property
    def encoding_ok(self):
        """True when every field that is supposed to be TEXT decoded."""
        return not (self.undecodable - self.BINARY_FIELDS)

    def has_memo_fields(self):
        return any(f[1] == "M" for f in self.fields)

    def read_memo(self, raw):
        """Return (text, status). status is 'ok', 'null', or a reason string.

        The pointer encoding is decided by the FIELD WIDTH, not by inspecting the
        bytes. Width 4 is a binary little-endian block number (FoxPro/VFP); width
        10 is the block number written as ASCII digits (dBASE III). Sniffing the
        content instead -- "are these bytes all digits?" -- is wrong and fails
        rarely enough to be nasty: a binary pointer of 0x34333231 is the four
        ASCII characters "1234", so it would silently resolve to block 1234
        rather than 825373492 and return some unrelated record's memo. That only
        bites once a file grows past roughly the first 0x30303030 blocks, so it
        passes every small test and corrupts large ones.
        """
        if self.memo is None:
            return None, "no sidecar file found"
        if self.blocksize == 0:
            return None, "sidecar declares block size 0"
        try:
            if len(raw) == 4:
                block = struct.unpack("<I", raw)[0]
            else:
                s = self._dec(raw).strip("\0 ")
                if not s:
                    return None, "null"
                if not s.isdigit():
                    return None, "non-numeric ASCII block pointer %r" % s
                block = int(s)
        except (ValueError, struct.error):
            return None, "unparseable block pointer %r" % raw
        if block == 0:
            return None, "null"
        p = block * self.blocksize
        if p + 8 > len(self.memo):
            return None, "block %d past end of sidecar" % block
        _typ, ln = struct.unpack(">II", self.memo[p:p + 8])
        if p + 8 + ln > len(self.memo):
            return None, "block %d claims %d bytes, sidecar has %d" % (
                block, ln, len(self.memo) - p - 8)
        return self._dec(self.memo[p + 8:p + 8 + ln], self._cur), "ok"

    def rows(self):
        p = self.hlen
        for i in range(self.nrec):
            rec = self.d[p:p + self.rlen]
            p += self.rlen
            if len(rec) < self.rlen:
                return
            o = 1
            row = {"_REC": i + 1, "_DELETED": rec[0:1] == b"*", "_MEMO_ERR": []}
            for name, typ, w, _dec in self.fields:
                raw = rec[o:o + w]
                o += w
                if typ in self.BINARY_TYPES:
                    row[name] = self._binary_value(typ, raw)
                    continue
                if typ == "M":
                    self._cur = name
                    txt, status = self.read_memo(raw)
                    if status not in ("ok", "null"):
                        row["_MEMO_ERR"].append("%s: %s" % (name, status))
                    row[name] = txt or ""
                else:
                    row[name] = self._dec(raw, name).strip()
            yield row


def cmd_struct(t):
    print("FILE     : %s" % t.path)
    print("VERSION  : 0x%02X" % t.version)
    print("RECORDS  : %d" % t.nrec)
    print("HEADER   : %d bytes    RECORD: %d bytes" % (t.hlen, t.rlen))
    print("WIDTHS   : fields+flag = %d  %s" % (
        t.width_sum, "matches record length" if t.width_ok
        else "*** MISMATCH vs %d -- header misread, rows would be skewed" % t.rlen))
    if t.has_memo_fields():
        if t.memo is None:
            print("MEMO     : *** %d memo fields but NO sidecar found -- every memo"
                  " will read empty, which is not the same as being empty"
                  % sum(1 for f in t.fields if f[1] == "M"))
        else:
            print("MEMO     : %s  (%d bytes, block size %d)"
                  % (t.memo_path, len(t.memo), t.blocksize))
    print()
    print("  %-12s %-4s %6s %4s" % ("FIELD", "TYPE", "WIDTH", "DEC"))
    for name, typ, w, dec in t.fields:
        print("  %-12s %-4s %6d %4d" % (name, typ, w, dec))

    if t.has_memo_fields() and t.nrec:
        print()
        print("  memo occupancy (so that empty is a count, not a silence):")
        counts = {f[0]: 0 for f in t.fields if f[1] == "M"}
        errs = 0
        for row in t.rows():
            errs += len(row["_MEMO_ERR"])
            for k in counts:
                if row[k]:
                    counts[k] += 1
        for k in sorted(counts, key=lambda x: -counts[x]):
            print("    %-12s non-empty in %3d of %d" % (k, counts[k], t.nrec))
        if errs:
            print("    *** %d memo read errors -- see `rows` mode" % errs)


def cmd_rows(t):
    if not t.nrec:
        print("(0 records)")
        return
    for row in t.rows():
        mark = "*" if row["_DELETED"] else " "
        print("%s%-5d" % (mark, row["_REC"]))
        for name, typ, _w, _d in t.fields:
            v = row[name]
            if typ == "M" and v:
                v = v.replace("\r\n", "\n")
                first = v.split("\n")
                print("    %-12s : %s" % (name, first[0]))
                for ln in first[1:]:
                    print("    %-12s   %s" % ("", ln))
            else:
                print("    %-12s : %s" % (name, v))
        for e in row["_MEMO_ERR"]:
            print("    *** MEMO ERROR %s" % e)


def cmd_form(t):
    missing = [c for c in FORM_COLS if c not in [f[0] for f in t.fields]]
    if missing:
        print("not an object table: missing columns %s" % ", ".join(missing))
        print("(use `struct` or `rows`)")
        return 2

    rows = list(t.rows())
    objs = [r for r in rows if r["PLATFORM"] != "COMMENT"]
    comments = [r for r in rows if r["PLATFORM"] == "COMMENT"]
    print("%d records: %d objects, %d COMMENT records (NOT objects; a loop that"
          " treats every record as one emits phantom controls)"
          % (len(rows), len(objs), len(comments)))

    census = {}
    for r in objs:
        census[r["BASECLASS"]] = census.get(r["BASECLASS"], 0) + 1
    print("\nbaseclass census (the portable vocabulary):")
    for k in sorted(census, key=lambda x: -census[x]):
        print("  %-18s %d" % (k or "(none)", census[k]))

    ext = sorted({r["CLASSLOC"] for r in objs if r["CLASSLOC"]})
    if ext:
        print("\nexternal class libraries -- this file is NOT self-contained:")
        for e in ext:
            print("  %s" % e)

    # Identity is the FULL DOTTED PATH, never OBJNAME. OBJNAME is not unique:
    # a grid with three columns yields three records all called "Header1" and
    # three more all called "Text1", distinguished only by their PARENT. PARENT
    # is itself sometimes a dotted path ("form1.grdPayment_methods.Column1"),
    # so neither end of the relation is a bare name.
    def fullpath(r):
        return (r["PARENT"] + "." + r["OBJNAME"]) if r["PARENT"] else r["OBJNAME"]

    kids = {}
    for r in objs:
        kids.setdefault(r["PARENT"], []).append(r)
    known = {fullpath(r) for r in objs}

    dupes = {}
    for r in objs:
        dupes[r["OBJNAME"]] = dupes.get(r["OBJNAME"], 0) + 1
    repeated = {k: v for k, v in dupes.items() if v > 1}
    if repeated:
        print("\nOBJNAME is NOT unique -- identity is the dotted path:")
        for k in sorted(repeated):
            print("  %-14s appears %d times" % (k, repeated[k]))

    # Objects that are referenced as a parent but have no record of their own.
    # In VFP these are created by a COUNT property on the parent (ColumnCount,
    # PageCount, ButtonCount), so part of the object tree is generated by
    # property VALUES rather than described by records. A reader that only walks
    # records loses every child of one.
    implicit = sorted(p for p in kids if p and p not in known)

    def walk(path, depth):
        for r in sorted(kids.get(path, []), key=lambda x: x["OBJNAME"]):
            extra = ("  class=" + r["CLASS"]) if r["CLASS"] != r["BASECLASS"] else ""
            print("%s%s  [%s]%s" % ("  " * depth, r["OBJNAME"], r["BASECLASS"], extra))
            for ln in r["PROPERTIES"].replace("\r\n", "\n").split("\n"):
                if ln.strip():
                    print("%s    %s" % ("  " * depth, ln.strip()))
            if r["METHODS"] or r["OBJCODE"]:
                print("%s    <code: METHODS %d B, OBJCODE %d B>"
                      % ("  " * depth, len(r["METHODS"]), len(r["OBJCODE"])))
            if r["OLE"] or r["OLE2"]:
                print("%s    <OLE payload: %d B + %d B -- opaque, not portable>"
                      % ("  " * depth, len(r["OLE"]), len(r["OLE2"])))
            here = fullpath(r)
            walk(here, depth + 1)
            for imp in implicit:
                if imp.startswith(here + ".") and "." not in imp[len(here) + 1:]:
                    print("%s  %s  [IMPLICIT -- no record; created by a count "
                          "property on the parent]" % ("  " * depth, imp.rsplit(".", 1)[1]))
                    walk(imp, depth + 2)

    print("\nobject tree (records are flat; PARENT may be a dotted path):")
    walk("", 1)

    unreachable = [i for i in implicit
                   if not any(i.startswith(k + ".") for k in known)]
    if unreachable:
        print("\nimplicit parents NOT reachable from any record:")
        for o in unreachable:
            print("  %s" % o)
    return 0


MENU_COLS = ("OBJTYPE", "OBJCODE", "NAME", "PROMPT", "COMMAND", "PROCEDURE",
             "LEVELNAME", "ITEMNUM", "NUMITEMS")


def cmd_menu(t):
    """.MNX only. Parenting here is LEVELNAME + ITEMNUM, NOT the PARENT column
    an .SCX uses. The two designer formats share a container (DBF) and share
    nothing about how they express structure."""
    have = {f[0] for f in t.fields}
    missing = [c for c in MENU_COLS if c not in have]
    if missing:
        print("not a menu table: missing columns %s" % ", ".join(missing))
        return 2

    rows = list(t.rows())
    header = [r for r in rows if r["OBJTYPE"] == "1"]
    conts = [r for r in rows if r["OBJTYPE"] == "2"]
    items = [r for r in rows if r["OBJTYPE"] == "3"]
    other = [r for r in rows if r["OBJTYPE"] not in ("1", "2", "3")]

    print("%d records: %d file-header, %d containers, %d items%s"
          % (len(rows), len(header), len(conts), len(items),
             ", %d UNCLASSIFIED" % len(other) if other else ""))

    for h in header:
        print("\nfile header: NAME=%s OBJCODE=%s LOCATION=%s"
              % (h["NAME"], h["OBJCODE"], h["LOCATION"]))
        if h["SETUP"]:
            print("  SETUP (%d B) emitted verbatim ahead of the menu definition:"
                  % len(h["SETUP"]))
            for ln in h["SETUP"].replace("\r\n", "\n").split("\n"):
                if ln.strip():
                    print("    %s" % ln.rstrip())
        if h["CLEANUP"]:
            print("  CLEANUP (%d B)" % len(h["CLEANUP"]))

    for c in sorted(conts, key=lambda r: r["LEVELNAME"]):
        kids = sorted((r for r in items if r["LEVELNAME"] == c["LEVELNAME"]),
                      key=lambda r: int(r["ITEMNUM"] or 0))
        print("\ncontainer %-14s OBJCODE=%-3s declares NUMITEMS=%-3s found=%d%s"
              % (c["NAME"], c["OBJCODE"], c["NUMITEMS"], len(kids),
                 "   *** COUNT MISMATCH" if c["NUMITEMS"].strip()
                 and int(c["NUMITEMS"]) != len(kids) else ""))
        if c["SCHEME"].strip():
            print("  COLOR SCHEME %s" % c["SCHEME"])
        if c["PROCEDURE"]:
            print("  popup-level PROCEDURE (%d B): %s"
                  % (len(c["PROCEDURE"]), c["PROCEDURE"].split("\n")[0][:70]))
        for r in kids:
            prompt = r["PROMPT"]
            kind = "SEPARATOR" if prompt.strip() == "\\-" else ""
            mnem = "mnemonic" if "\\<" in prompt else ""
            action = r["COMMAND"] or r["PROCEDURE"]
            tag = "COMMAND" if r["COMMAND"] else ("PROCEDURE" if r["PROCEDURE"] else "none")
            print("  %3s  %-24s %-9s %-9s %s"
                  % (r["ITEMNUM"], prompt or "(no prompt)", kind or mnem, tag,
                     (action.split("\n")[0][:52]) if action else ""))
            if r["KEYNAME"]:
                print("       KEY %s (label %r)" % (r["KEYNAME"], r["KEYLABEL"]))
            if r["SKIPFOR"]:
                print("       SKIP FOR %s" % r["SKIPFOR"].split("\n")[0][:60])
            if r["MESSAGE"]:
                print("       MESSAGE %s" % r["MESSAGE"][:60])

    orphan = [r for r in items
              if r["LEVELNAME"] not in {c["LEVELNAME"] for c in conts}]
    if orphan:
        print("\nitems whose LEVELNAME matches no container:")
        for r in orphan:
            print("  %s in level %r" % (r["PROMPT"], r["LEVELNAME"]))
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        print("usage: read_vfp_binary.py <file> [struct|rows|form|menu]")
        return 2
    path = argv[1]
    mode = argv[2].lower() if len(argv) > 2 else "struct"
    if not os.path.exists(path):
        print("no such file: %s" % path, file=sys.stderr)
        return 2
    try:
        t = Dbf(path)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    if mode == "struct":
        cmd_struct(t)
    elif mode == "rows":
        cmd_rows(t)
    elif mode == "form":
        return cmd_form(t)
    elif mode == "menu":
        return cmd_menu(t)
    else:
        print("unknown mode %r (struct|rows|form|menu)" % mode, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
