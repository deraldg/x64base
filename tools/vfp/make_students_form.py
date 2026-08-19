#!/usr/bin/env python3
"""Emit X64FORM.SCX/.SCT -- a self-contained form over the x64base STUDENTS table.

Owner: member.derald. Author: member.ai.claude.cowork. Lane: AIF-120. 2026-08-18.

The AIF-120 experiment: this project generates an .SCX and Microsoft's Form
Designer is asked to open it. The reference to be structurally like is
tools/vfp/fixtures/STUDENTS.SCX -- VFP's own wizard output over the SAME table.

Scope is deliberately the easy case (R6): form, dataenvironment/cursor, labels
and textboxes. Native base classes with CLASSLOC empty, so the file is
self-contained under R1 and needs no .VCX on the opening machine.

Geometry note, and it is the point of R12: this writer emits Left/Top/Width and
NO Height on labels and textboxes -- the same partiality VFP's wizard emits in
42 of 42 geometry-bearing records across the two wizard specimens. If the
designer opens this, that partiality is confirmed as something a real consumer
accepts, not merely something a producer happens to emit.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from write_vfp_binary import FormBuilder, write_scx

FIELDS = [
    ("SID",      "Sid:"),
    ("LNAME",    "Lname:"),
    ("FNAME",    "Fname:"),
    ("DOB",      "Dob:"),
    ("GENDER",   "Gender:"),
    ("MAJOR",    "Major:"),
    ("ENROLL_D", "Enroll_d:"),
    ("GPA",      "Gpa:"),
    ("EMAIL",    "Email:"),
]

def build(out_dir):
    f = FormBuilder(name="Form1", caption="STUDENTS (x64base-generated)",
                    table="students", width=520, height=338,
                    fonts=["Arial, 0, 9, 5, 15, 12, 32, 3, 0"])
    top = 20
    for field, caption in FIELDS:
        f.label("LBL" + field, caption, left=10, top=top + 4, width=60)
        f.textbox(field + "1", field, left=80, top=top, width=200)
        top += 28
    scx = os.path.join(out_dir, "X64FORM.SCX")
    sct = os.path.join(out_dir, "X64FORM.SCT")
    n, rlen, hlen = write_scx(scx, sct, f.records())
    print("wrote %s  records=%d rlen=%d hlen=%d bytes=%d"
          % (scx, n, rlen, hlen, os.path.getsize(scx)))
    print("wrote %s  bytes=%d" % (sct, os.path.getsize(sct)))
    return scx, sct

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
