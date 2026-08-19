#!/usr/bin/env python3
"""UIDEF v1 -- the AIF-120 design table, as a real DBF with a memo sidecar.

Contract: docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
Owner: member.derald. Author: member.ai.claude.cowork. Lane: AIF-120. 2026-08-19.
Python 3 stdlib only, per AIF-085.

The point of writing this is that a contract nobody has produced from is a
hypothesis. Section 5b of the contract exists because this file was attempted.
"""
import datetime as dt
import struct

# The v1 schema from the contract, section 3. Order is not significant to a
# conformant reader; it is fixed here only so output is byte-stable.
FIELDS = [
    ("RECKIND",    "C",  4),
    ("OBJID",      "C", 12),
    ("PARENT",     "C", 12),
    ("ORDINAL",    "N",  5),
    # Tab order is a SECOND ordinal over the same children, not an attribute of
    # one of them. Measured 2026-08-19 across 171 corpus groups and 1689 tab
    # stops: it matches document order in 5.3% and banded reading order in 25.7%,
    # so it is not derivable from anything else in the table. Owner's call, taken
    # in-session: an ordinal, not a PROPS property.
    ("TABORDINAL", "N",  5),
    ("SPAN",       "N",  5),
    ("KIND",       "C", 20),
    ("FLOW",       "C",  8),
    ("BINDING",    "C", 64),
    ("FONTREF",    "N",  3),
    ("PROVENANCE", "C", 10),
    ("PROPS",      "M",  4),
    ("ORIGIN",     "M",  4),
    ("HANDLERS",   "M",  4),
    ("SOURCE",     "M",  4),
    ("NOTES",      "M",  4),
]

KINDS = {"form","panel","group","pageset","page",
         "label","text","button","check","radio","list","combo","image","menu"}
FLOWS = {"row","column","grid","free"}
# R33. The header declares a codepage in byte 29 and every value was then encoded
# as latin1, which is a DIFFERENT encoding across 0x80-0x9F -- so a euro sign or a
# curly quote, both ordinary in the de/fr/es/it text x64base's own message catalog
# already ships, raised UnicodeEncodeError instead of being written. Declare and
# encode with the SAME codepage, and say which character failed when one will not
# fit.
LANGUAGE_DRIVER = {"cp1252": 0x03, "cp1250": 0xc8, "cp1251": 0xc9, "cp1253": 0xcb,
                   "cp1254": 0xca, "cp1255": 0x7d, "cp1256": 0x7e, "cp874": 0x7c,
                   "cp932": 0x7b, "cp936": 0x7a, "cp949": 0x79, "cp950": 0x78}
DEFAULT_ENCODING = "cp1252"
BACKLINK = 263
MEMO_START = 512


class Memo:
    def __init__(self, start=MEMO_START, encoding=DEFAULT_ENCODING):
        self.blocks=[]; self.offset=start; self.start=start; self.encoding=encoding
    def add(self, text):
        if not text: return 0
        p=encode_or_explain(text, self.encoding); ptr=self.offset
        self.blocks.append(struct.pack(">II",1,len(p))+p)
        self.offset += 8+len(p)
        return ptr
    def bytes(self):
        body=b"".join(self.blocks)
        return (struct.pack(">I", self.start+len(body)) + b"\0\0"
                + struct.pack(">H",1) + b"\0"*(self.start-8) + body)


def encode_or_explain(text, encoding, where=""):
    """Encode, or fail naming the character AND the codepage that cannot hold it.

    `UnicodeEncodeError: 'latin-1' codec can't encode character '\u0119'` tells a
    caller nothing actionable. A DBF carries ONE codepage, so the honest failure is
    "this document is cp1252 and this character is not in it" -- which is a real
    constraint of the container, not a bug to be worked around silently.
    """
    try:
        return text.encode(encoding)
    except UnicodeEncodeError as e:
        bad = text[e.start:e.end]
        raise ValueError(
            "%scannot store %r (U+%04X) in a %s table: a DBF declares one codepage "
            "in header byte 29 and every value must fit it"
            % (where and where + ": ", bad, ord(bad[0]), encoding))


def props(pairs):
    return "".join("%s = %s\r\n" % (k,v) for k,v in pairs)


def write(dbf_path, fpt_path, records, today=None, encoding=DEFAULT_ENCODING):
    memo=Memo(encoding=encoding)
    rlen = 1 + sum(w for _,_,w in FIELDS)
    packed=[]
    for i,rec in enumerate(records):
        row=b" "
        for name,typ,w in FIELDS:
            v=rec.get(name,"")
            if typ=="M":
                row += struct.pack("<I", memo.add(v))
            elif typ=="N":
                s="" if v in ("",None) else str(int(v))
                row += s.encode("ascii")[:w].rjust(w,b" ")
            else:
                row += encode_or_explain(str(v), encoding,
                                         "record %d field %s" % (i+1, name))[:w].ljust(w,b" ")
        if len(row)!=rlen:
            raise ValueError("record %d is %d bytes, expected %d" % (i+1,len(row),rlen))
        packed.append(row)
    hlen = 32 + 32*len(FIELDS) + 1 + BACKLINK
    d = today or dt.date.today()
    h = bytes([0x30, d.year%100, d.month, d.day])
    h += struct.pack("<I", len(packed)) + struct.pack("<H", hlen) + struct.pack("<H", rlen)
    driver = LANGUAGE_DRIVER.get(encoding)
    if driver is None:
        raise ValueError("no VFP language driver byte for %r" % encoding)
    h += b"\0"*16 + bytes([0x02, driver]) + b"\0"*2
    disp=1
    for name,typ,w in FIELDS:
        fb = name.encode("ascii")[:11].ljust(11,b"\0") + typ.encode("ascii")
        fb += struct.pack("<I", disp) + bytes([w,0])
        h += fb.ljust(32,b"\0"); disp+=w
    h += b"\x0D" + b"\0"*BACKLINK
    if len(h)!=hlen: raise ValueError("header %d != declared %d" % (len(h),hlen))
    open(dbf_path,"wb").write(h + b"".join(packed) + b"\x1A")
    open(fpt_path,"wb").write(memo.bytes())
    return len(packed), rlen, hlen


def validate(rows):
    """Conformance checks from contract section 12. Returns a list of findings."""
    out=[]
    # TABORDINAL is an order over a container's children, so its only structural
    # rule is that two children of one container cannot share a position. A claim
    # that can be checked should be checked (R13's RESERVED2 principle, R22.1).
    tabs={}
    for i,r in enumerate(rows,1):
        if (r.get("RECKIND") or "").strip()!="OBJ": continue
        t=(str(r.get("TABORDINAL") or "").strip())
        if not t or t=="0": continue
        par=(r.get("PARENT") or "").strip()
        # A top-level object is its own tab domain. An .SCX can hold a form SET --
        # several forms in one file -- and each starts its tab sequence at 1, so
        # comparing them to each other is a false positive. The first version of
        # this check did exactly that, and most of what it flagged was form sets.
        if not par: continue
        key=(par, t)
        if key in tabs:
            out.append("rec %d: TABORDINAL %s duplicated in container %r (also rec %d)"
                       % (i, t, key[0], tabs[key]))
        tabs[key]=i
    if not rows or (rows[0].get("RECKIND") or "").strip()!="DOC":
        out.append("section 2: first record must be RECKIND=DOC")
    seen=set()
    for i,r in enumerate(rows,1):
        k=(r.get("RECKIND") or "").strip()
        oid=(r.get("OBJID") or "").strip()
        if k not in ("DOC","FONT","OBJ"): out.append("rec %d: RECKIND %r not in DOC/FONT/OBJ" % (i,k))
        if not oid: out.append("rec %d: OBJID required to produce (P)" % i)
        if oid in seen: out.append("rec %d: OBJID %r is not unique" % (i,oid))
        seen.add(oid)
        if k=="OBJ":
            kind=(r.get("KIND") or "").strip().lower()
            if kind not in KINDS: out.append("rec %d: KIND %r not in the v1 vocabulary" % (i,kind))
            if not (r.get("PROVENANCE") or "").strip():
                out.append("rec %d: PROVENANCE required to produce (P)" % i)
            fl=(r.get("FLOW") or "").strip().lower()
            if fl and fl not in FLOWS: out.append("rec %d: FLOW %r invalid" % (i,fl))
            org=(r.get("ORIGIN") or "")
            if "ORIGIN_" in org and "ORIGIN_SCALE" not in org:
                out.append("rec %d: section 8 -- ORIGIN_* present with no ORIGIN_SCALE" % i)
    return out
