#!/usr/bin/env python3
"""Write the DBF-shaped VFP designer binaries. Currently .SCX + .SCT.

Owner: member.derald. Author: member.ai.claude.cowork. Lane: AIF-120. 2026-08-18.
Python 3 stdlib only, per AIF-085.

The counterpart to read_vfp_binary.py, and the same premise: a form is a table of
objects, so writing one is writing a DBF with a memo sidecar. Every constant here
was measured off tools/vfp/fixtures/STUDENTS.SCX rather than recalled -- that file
is VFP 9 wizard output over an x64base-written table, so it is the reference this
writer is trying to be structurally indistinguishable from.

Layout, measured:

  .SCX header   byte 0   = 0x30            VFP table
                bytes1-3 = YY MM DD        last update
                bytes4-7 = record count, little-endian
                bytes8-9 = header length = 32 + 32*nfields + 1 + 263
                bytes10-11 = record length
                byte 28  = 0x02            a memo sidecar exists
                byte 29  = 0x03            codepage marker
                then nfields x 32-byte descriptors, 0x0D, 263 zero bytes
                then records, then 0x1A

  .SCT          bytes0-3 = next free byte offset, BIG-endian
                bytes6-7 = block size, BIG-endian, = 1 (so a block number IS a
                           byte offset -- this is why .SCT pointers look huge)
                blocks start at 512; each is >II (type=1, length) then payload,
                packed contiguously with no alignment padding.

R1 is why this writer emits native base classes and leaves CLASSLOC empty: a form
keyed on BASECLASS with no external .VCX is self-contained, and self-contained is
the only kind of form this project can honestly generate.
"""

import datetime as dt
import struct
import sys

# Measured off STUDENTS.SCX: 23 fields, record length 109.
SCX_FIELDS = [
    ("PLATFORM",  "C",  8),
    ("UNIQUEID",  "C", 10),
    ("TIMESTAMP", "N", 10),
    ("CLASS",     "M",  4),
    ("CLASSLOC",  "M",  4),
    ("BASECLASS", "M",  4),
    ("OBJNAME",   "M",  4),
    ("PARENT",    "M",  4),
    ("PROPERTIES","M",  4),
    ("PROTECTED", "M",  4),
    ("METHODS",   "M",  4),
    ("OBJCODE",   "M",  4),
    ("OLE",       "M",  4),
    ("OLE2",      "M",  4),
    ("RESERVED1", "M",  4),
    ("RESERVED2", "M",  4),
    ("RESERVED3", "M",  4),
    ("RESERVED4", "M",  4),
    ("RESERVED5", "M",  4),
    ("RESERVED6", "M",  4),
    ("RESERVED7", "M",  4),
    ("RESERVED8", "M",  4),
    ("USER",      "M",  4),
]

BACKLINK = 263          # VFP's database-container backlink block
MEMO_START = 512        # first usable .SCT block offset, as VFP writes it
SCREEN_VERSION = "VERSION =   3.00"


class MemoFile:
    """Accumulates .SCT blocks. Returns the byte offset to store in the record."""

    def __init__(self, start=MEMO_START):
        self.blocks = []
        self.offset = start
        self.start = start

    def add(self, text):
        """Store `text`; return its block pointer, or 0 for nothing to store."""
        if text is None or text == "":
            return 0
        payload = text.encode("latin1")
        ptr = self.offset
        self.blocks.append(struct.pack(">II", 1, len(payload)) + payload)
        self.offset += 8 + len(payload)
        return ptr

    def bytes(self):
        body = b"".join(self.blocks)
        head = struct.pack(">I", self.start + len(body)) + b"\0\0" + struct.pack(">H", 1)
        return head + b"\0" * (self.start - 8) + body


def _descriptor(name, typ, width, disp):
    b = name.encode("ascii")[:11].ljust(11, b"\0")
    b += typ.encode("ascii")
    b += struct.pack("<I", disp)
    b += bytes([width, 0])
    return b.ljust(32, b"\0")


def write_scx(scx_path, sct_path, records, today=None):
    """records: list of dicts keyed by SCX_FIELDS names. Memo fields hold text."""
    memo = MemoFile()
    rlen = 1 + sum(w for _, _, w in SCX_FIELDS)

    packed = []
    for rec in records:
        row = b" "                      # not-deleted flag
        for name, typ, width in SCX_FIELDS:
            v = rec.get(name, "")
            if typ == "M":
                row += struct.pack("<I", memo.add(v))
            else:
                row += str(v).encode("latin1")[:width].ljust(width, b" ")
        if len(row) != rlen:
            raise ValueError("record %d packed to %d bytes, expected %d"
                             % (len(packed) + 1, len(row), rlen))
        packed.append(row)

    hlen = 32 + 32 * len(SCX_FIELDS) + 1 + BACKLINK
    d = today or dt.date.today()
    head = bytes([0x30, d.year % 100, d.month, d.day])
    head += struct.pack("<I", len(packed))
    head += struct.pack("<H", hlen)
    head += struct.pack("<H", rlen)
    head += b"\0" * 16
    head += bytes([0x02, 0x03])         # memo present; codepage marker
    head += b"\0" * 2

    disp = 1
    for name, typ, width in SCX_FIELDS:
        head += _descriptor(name, typ, width, disp)
        disp += width
    head += b"\x0D" + b"\0" * BACKLINK

    if len(head) != hlen:
        raise ValueError("header built to %d bytes, declared %d" % (len(head), hlen))

    with open(scx_path, "wb") as fh:
        fh.write(head + b"".join(packed) + b"\x1A")
    with open(sct_path, "wb") as fh:
        fh.write(memo.bytes())
    return len(packed), rlen, hlen


# ---------------------------------------------------------------- form builder

def _props(pairs):
    return "".join("%s = %s\r\n" % (k, v) for k, v in pairs)


class FormBuilder:
    """Builds the record list for a simple, self-contained, native-baseclass form.

    Deliberately narrow: form, dataenvironment/cursor, labels and textboxes. R6's
    implicit-children rule means grids, pageframes and button groups are a harder
    problem and are out of scope until this one is proven against the designer.
    """

    def __init__(self, name, caption, table, width, height, fonts=None):
        self.name, self.caption, self.table = name, caption, table
        self.width, self.height = width, height
        self.fonts = fonts or ["Arial, 0, 9, 5, 15, 12, 32, 3, 0"]
        self.controls = []
        self._uid = 0

    def uid(self):
        self._uid += 1
        return "_X64B%05d" % self._uid

    def label(self, name, caption, left, top, width):
        self.controls.append(("label", name, [
            ("Caption", '"%s"' % caption), ("Left", left), ("Top", top),
            ("Visible", ".T."), ("Width", width), ("Name", '"%s"' % name)]))

    def textbox(self, name, field, left, top, width):
        self.controls.append(("textbox", name, [
            ("ControlSource", '"%s.%s"' % (self.table, field)),
            ("Left", left), ("Top", top), ("Visible", ".T."),
            ("Width", width), ("Name", '"%s"' % name)]))

    def records(self):
        blank = {}
        recs = [dict(blank, PLATFORM="COMMENT", UNIQUEID="Screen",
                     RESERVED1=SCREEN_VERSION)]

        def obj(baseclass, objname, parent, pairs, cls=None):
            # CLASS is NOT optional on output, even though R1 says an importer may
            # ignore it. Measured: all three specimens populate CLASS on every
            # record, and the native form1.scx sets CLASS = BASECLASS where there
            # is no styling class. Leaving it empty makes VFP 9 refuse the file
            # with "Parent : Class name is invalid" on the first such record.
            # R1 is asymmetric: optional to consume, mandatory to produce.
            return dict(PLATFORM="WINDOWS", UNIQUEID=self.uid(), TIMESTAMP="",
                        CLASS=cls or baseclass,
                        BASECLASS=baseclass, OBJNAME=objname, PARENT=parent,
                        PROPERTIES=_props(pairs))

        # RESERVED2 is the record count for this definition block -- KB Q145742,
        # "counts records associated with a class definition". Measured as "2" on
        # the DataEnvironment record of all three specimens (itself + one cursor).
        # Omitting it appears to leave VFP unable to close the DataEnvironment
        # block, so the next container it sees is not the form.
        de = obj("dataenvironment", "Dataenvironment", "", [
            ("Visible", ".F."), ("TabStop", ".F."), ("DataSource", ".NULL."),
            ("Name", '"Dataenvironment"')])
        de["RESERVED2"] = str(1 + 1)          # this record plus its one cursor
        recs.append(de)
        recs.append(obj("cursor", "CURSOR1", "Dataenvironment", [
            ("Alias", '"%s"' % self.table),
            ("CursorSource", "%s.dbf" % self.table),
            ("Name", '"CURSOR1"')]))
        recs.append(obj("form", self.name, "", [
            ("ScaleMode", 3), ("Height", self.height), ("Width", self.width),
            ("DoCreate", ".T."), ("Caption", '"%s"' % self.caption),
            ("Name", '"%s"' % self.name)]))
        for baseclass, objname, pairs in self.controls:
            recs.append(obj(baseclass, objname, self.name, pairs))

        recs.append(dict(blank, PLATFORM="COMMENT", UNIQUEID="RESERVED",
                         PROPERTIES="".join(f + "\n" for f in self.fonts)))
        return recs


if __name__ == "__main__":
    print(__doc__)
    print("This module is a library; see make_students_form.py for a caller.")
    sys.exit(0)
