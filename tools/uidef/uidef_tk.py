#!/usr/bin/env python3
"""Gate 11 spike -- build a Tk window from a UIDEF table and NOTHING else.

AIF-120. Owner: member.derald. Author: member.ai.claude.cowork. 2026-08-19.

The acceptance test for the gate 10 contract is whether a frontend can be
generated from the design table alone. So this file deliberately knows nothing
about VFP, .SCX, or any other part of this project. Its whole input is:

  * a DBF with a memo sidecar
  * docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md

Tk is chosen because the charter calls it the least representative of the target
set -- "not thread-safe at all", geometry by pack/grid/place -- so it is the
least flattering backend available.

  python uidef_tk.py <UIDEF.DBF>            # render
  python uidef_tk.py <UIDEF.DBF> --dump     # headless: print the widget tree

Headless capture, as used to produce the evidence image (needs xvfb + ImageMagick,
and a Python with tkinter -- 3.12 here, 3.11 has none):

  xvfb-run -s "-screen 0 620x420x24" python3.12 uidef_tk.py UIDEF.DBF --shot out.png
"""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vfp_binary import Dbf

# R16: a stated ORIGIN size is ADVISORY for controls whose size their content
# determines, and AUTHORITATIVE for controls whose size the data determines.
# Evidence: docs/maintenance/evidence/AIF120_origin_abc.png -- honouring every
# width truncates labels, honouring none loses field sizing, honouring only the
# data-sized ones keeps both.
CONTENT_SIZED = {'label','button','check','radio','group','page'}
DATA_SIZED    = {'text','list','combo','image'}

KIND_WIDGET = {          # contract section 4, the fourteen v1 kinds
    'form':'toplevel', 'panel':'frame', 'group':'labelframe',
    'pageset':'notebook', 'page':'frame',
    'label':'Label', 'text':'Entry', 'button':'Button', 'check':'Checkbutton',
    'radio':'Radiobutton', 'list':'Listbox', 'combo':'Combobox', 'image':'Label',
    'menu':'menu',
}


def parse_props(txt):
    d = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            d[k.strip().lower()] = v.strip().strip('"')
    return d


def load(path):
    rows = list(Dbf(path).rows())
    doc = [r for r in rows if (r['RECKIND'] or '').strip() == 'DOC']
    fonts = [r for r in rows if (r['RECKIND'] or '').strip() == 'FONT']
    objs = [r for r in rows if (r['RECKIND'] or '').strip() == 'OBJ']
    if not doc:
        raise SystemExit("not a UIDEF table: no DOC record (contract s2)")
    return doc[0], fonts, objs


def tree(objs):
    kids = {}
    for r in objs:
        kids.setdefault((r['PARENT'] or '').strip(), []).append(r)
    for k in kids:
        kids[k].sort(key=lambda r: int((r['ORDINAL'] or '0').strip() or 0))
    return kids


def describe(path):
    doc, fonts, objs = load(path)
    kids = tree(objs)
    print("UIDEF document: %s" % os.path.basename(path))
    print("  DOC props:", parse_props(doc['PROPS']))
    print("  FONT rows: %d   OBJ rows: %d" % (len(fonts), len(objs)))
    refused = []

    def walk(pid, depth):
        for r in kids.get(pid, []):
            kind = (r['KIND'] or '').strip().lower()
            w = KIND_WIDGET.get(kind)
            org = parse_props(r['ORIGIN']); pr = parse_props(r['PROPS'])
            hs = parse_props(r['HANDLERS'])
            if not w:
                refused.append(kind)
            pos = ""
            if 'origin_top' in org:
                pos = " place(x=%s,y=%s" % (org.get('origin_left', '0'), org['origin_top'])
                if 'origin_width' in org:
                    pos += ",w=%s" % org['origin_width']
                pos += ") unit=%s" % org.get('origin_scale', '?')
            print("   %s%-9s %-11s %-22s%s%s" % (
                "  " * depth, (r['OBJID'] or '').strip(), kind,
                (w or '<<REFUSED>>') + " ",
                (" text=%r" % pr['caption'] if 'caption' in pr else ""), pos))
            if hs:
                print("   %s      handlers: %s" % ("  " * depth, hs))
            walk((r['OBJID'] or '').strip(), depth + 1)

    walk("", 0)
    if refused:
        print("  REFUSED kinds:", sorted(set(refused)))


def build_window(path):
    import tkinter as tk
    from tkinter import ttk
    doc, fonts, objs = load(path)
    kids = tree(objs)
    root = tk.Tk()
    root.title(parse_props(doc['PROPS']).get('sourcefile', 'UIDEF'))
    made = {}

    def build(pid, parent):
        for r in kids.get(pid, []):
            oid = (r['OBJID'] or '').strip()
            kind = (r['KIND'] or '').strip().lower()
            pr = parse_props(r['PROPS']); org = parse_props(r['ORIGIN'])
            flow = (r['FLOW'] or '').strip().lower()
            cap = pr.get('caption', '')
            if kind == 'form':
                if 'origin_height' in org:
                    root.geometry("%dx%d" % (int(float(org.get('origin_width', 520))),
                                             int(float(org['origin_height'])) + 20))
                if cap:
                    root.title(cap)
                made[oid] = root
                build(oid, root)
                continue
            factory = {
                'label':  lambda: ttk.Label(parent, text=cap),
                'text':   lambda: ttk.Entry(parent),
                'button': lambda: ttk.Button(parent, text=cap or oid),
                'check':  lambda: ttk.Checkbutton(parent, text=cap),
                'radio':  lambda: ttk.Radiobutton(parent, text=cap),
                'list':   lambda: tk.Listbox(parent, height=4),
                'combo':  lambda: ttk.Combobox(parent),
                'image':  lambda: ttk.Label(parent, text="[image]"),
                'panel':  lambda: ttk.Frame(parent, relief='groove', borderwidth=1),
                'page':   lambda: ttk.Frame(parent),
                'group':  lambda: ttk.LabelFrame(parent, text=cap),
            }.get(kind)
            if factory is None:
                print("REFUSED kind %r on %s -- contract s4" % (kind, oid))
                continue
            w = factory()
            # Contract s8: a generator that honours ORIGIN must honour ORIGIN_SCALE.
            # Position is honoured; SIZE is filtered by R16 -- honouring a label's
            # stated width truncates it on a toolkit with a different font.
            if 'origin_top' in org and 'origin_left' in org:
                kw = dict(x=float(org['origin_left']), y=float(org['origin_top']))
                if 'origin_width' in org and kind not in CONTENT_SIZED:
                    kw['width'] = float(org['origin_width'])   # R16
                w.place(**kw)
            elif flow == 'row':
                w.pack(side='left')
            else:
                w.pack(anchor='w')
            made[oid] = w
            build(oid, w)

    build("", root)
    return root, made


if __name__ == '__main__':
    p = sys.argv[1]
    if '--dump' in sys.argv:
        describe(p)
    elif '--shot' in sys.argv:
        out = sys.argv[sys.argv.index('--shot') + 1]
        root, made = build_window(p)
        root.update_idletasks(); root.update(); time.sleep(0.6)
        subprocess.run(["import", "-window", "root", out], check=False)
        print("rendered %d widgets -> %s" % (len(made), out))
    else:
        build_window(p)[0].mainloop()
