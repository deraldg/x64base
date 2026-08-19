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

# The kinds THIS target renders. Exposed as a constant so a conformance check can
# import it rather than keep a second opinion about what Tk supports -- the failure
# mode R22.1 and R23.4 both landed on.
KINDS_RENDERED = frozenset((
    'form', 'label', 'text', 'button', 'check', 'radio', 'list', 'combo',
    'image', 'panel', 'page', 'group', 'pageset',
))
FLOWS_SUPPORTED = frozenset(('row', 'column', 'grid', 'free'))
DISPATCH_SUPPORTED = frozenset(('ui', 'worker', 'host'))
DATA_SIZED    = {'text','list','combo','image'}

KIND_WIDGET = {          # contract section 4, the fourteen v1 kinds
    'form':'toplevel', 'panel':'frame', 'group':'labelframe',
    'pageset':'notebook', 'page':'frame',
    'label':'Label', 'text':'Entry', 'button':'Button', 'check':'Checkbutton',
    'radio':'Radiobutton', 'list':'Listbox', 'combo':'Combobox', 'image':'Label',
    'menu':'menu',
}


def parse_handlers_line(txt):
    """`Event = Name / dispatch [-> Completion]` -- contract section 9."""
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if '=' not in line:
            continue
        ev, rest = line.split('=', 1)
        comp = None
        if '->' in rest:
            rest, comp = rest.split('->', 1)
            comp = comp.strip()
        parts = [p.strip() for p in rest.split('/')]
        out[ev.strip()] = (parts[0], (parts[1] if len(parts) > 1 else 'ui').lower(), comp)
    return out


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


def build_window(path, registry=None, host=None):
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font as tkfont
    doc, fonts, objs = load(path)
    kids = tree(objs)
    rec = {(r['OBJID'] or '').strip(): r for r in objs}

    # R37: the reference consumer uses the shared runtime rather than wiring
    # handlers itself. The lock domains come from the document's own SOURCE (R36),
    # so this backend never decides what to serialize against -- it is told.
    rt = scope = None
    if registry is not None:
        import uidef_runtime
        rt = uidef_runtime.Runtime(
            uidef_runtime.domains_from_source(doc['SOURCE']),
            registry, host=host)
        scope = uidef_runtime.Scope('window')
    root = tk.Tk()

    # FONTREF is a 1-based index into the document's FONT rows in table order
    # (contract field table). Until 2026-08-19 nothing resolved it -- FONT rows were
    # produced by the importer and consumed by nobody, which is how every object came
    # to point at cache line 1 without anyone noticing.
    fontobj = {}
    for i, fr in enumerate(fonts, 1):
        fp = parse_props(fr['PROPS'])
        fam = fp.get('name')
        try:
            size = int(float(fp.get('size') or 0))
        except ValueError:
            size = 0
        if fam and size:
            fontobj[i] = tkfont.Font(family=fam, size=size)
    root.title(parse_props(doc['PROPS']).get('sourcefile', 'UIDEF'))
    made = {}
    notes = []
    applied = []

    def container_flow(oid):
        # Contract section 5, field table line: FLOW is "P on containers". The
        # container declares how its children are arranged; the CHILD carries only
        # ORDINAL and SPAN. Reading FLOW off the child -- which this file did until
        # 2026-08-19 -- means `row` and `column` can never fire, because no importer
        # writes FLOW onto a child. That is why they had never been rendered.
        r = rec.get(oid)
        return (r['FLOW'] or '').strip().lower() if r is not None else ''

    def build(pid, parent):
        pflow = container_flow(pid)
        pkind = ((rec[pid]['KIND'] or '').strip().lower() if pid in rec else '')
        gcols = None
        if pflow == 'grid':
            gp = parse_props(rec[pid]['PROPS']) if pid in rec else {}
            if 'columns' in gp:
                gcols = int(float(gp['columns']))
            else:
                # Section 5 says `grid` wraps, and never says at what width. An
                # absent dimension is not defaulted to a number (R12.3), so the
                # container is refused and named rather than guessed at 2.
                notes.append("REFUSED grid on %s -- FLOW=grid with no Columns "
                             "property; section 5 does not say where it wraps" % pid)
                pflow = 'column'
        cell = [0, 0]
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
                # `pageset` is in the contract's vocabulary and import_scx maps
                # `pageframe` onto it, but this file had no factory for it, so the
                # reference consumer refused every tabbed form it was given. Found
                # by manifest.py on its first run over form1.scx.
                'pageset': lambda: ttk.Notebook(parent),
            }.get(kind)
            if factory is None:
                print("REFUSED kind %r on %s -- contract s4" % (kind, oid))
                continue
            assert kind in KINDS_RENDERED, (
                "%r renders but is not in KINDS_RENDERED -- the constant has drifted"
                % kind)
            w = factory()
            # Contract s8: a generator that honours ORIGIN must honour ORIGIN_SCALE.
            # Position is honoured; SIZE is filtered by R16 -- honouring a label's
            # stated width truncates it on a toolkit with a different font.
            span = int(float((r['SPAN'] or '0').strip() or 0)) or 1
            if pkind == 'pageset':
                # A tab is not placed by a geometry manager; the notebook owns it.
                parent.add(w, text=cap or oid)
            elif pflow == 'free' or not pflow:
                if 'origin_top' in org and 'origin_left' in org:
                    kw = dict(x=float(org['origin_left']), y=float(org['origin_top']))
                    # R16 says a stated dimension is advisory when CONTENT decides
                    # it. A container whose children are absolutely positioned has
                    # no content-determined size -- `place` does not propagate
                    # geometry, so the container collapses and clips everything in
                    # it. Found by R30: materialised option-group members rendered
                    # into a zero-size frame and vanished.
                    placed_kids = any((k['ORIGIN'] or '').strip()
                                      for k in kids.get(oid, []))
                    content_sized = kind in CONTENT_SIZED and not placed_kids
                    if 'origin_width' in org and not content_sized:
                        kw['width'] = float(org['origin_width'])   # R16
                    if 'origin_height' in org and placed_kids:
                        kw['height'] = float(org['origin_height'])
                    w.place(**kw)
                else:
                    # `free` means positioned by ORIGIN, and there is no ORIGIN. The
                    # only thing left is ORDINAL. R12.3: a target that derives a
                    # position must SAY it derived one.
                    notes.append("DERIVED position for %s -- FLOW=free with no "
                                 "ORIGIN; fell back to ORDINAL order" % oid)
                    w.pack(anchor='w')
            elif pflow == 'row':
                w.pack(side='left', padx=2, pady=2)
            elif pflow == 'column':
                w.pack(side='top', anchor='w', padx=2, pady=2)
            elif pflow == 'grid':
                if cell[1] + span > gcols:
                    cell[0] += 1; cell[1] = 0
                w.grid(row=cell[0], column=cell[1], columnspan=span,
                       sticky='w', padx=2, pady=2)
                cell[1] += span
                if cell[1] >= gcols:
                    cell[0] += 1; cell[1] = 0
            else:
                w.pack(anchor='w')
            try:
                fri = int(float((r['FONTREF'] or '0').strip() or 0))
            except ValueError:
                fri = 0
            if fri:
                f = fontobj.get(fri)
                if f is None:
                    notes.append("FONTREF %d on %s names no usable FONT row" % (fri, oid))
                else:
                    try:
                        w.configure(font=f)
                        applied.append((oid, fri))
                    except tk.TclError:
                        # ttk styles a Button's font through the style, not the
                        # widget. Say so rather than drop it silently.
                        notes.append("FONTREF %d on %s (%s): this toolkit will not "
                                     "take a font on that widget" % (fri, oid, kind))
            if rt is not None:
                hs = parse_handlers_line(r['HANDLERS'])
                click = hs.get('Click')
                if click:
                    name, disp, comp = click
                    alias = (r['BINDING'] or '').strip().split('.')[0]
                    try:
                        w.configure(command=(lambda n=name, d=disp, a=alias, c=comp:
                                             rt.fire(n, d, scope, alias=a,
                                                     completion=c)))
                    except tk.TclError:
                        pass                      # not a command widget
            made[oid] = w
            build(oid, w)

    build("", root)
    if rt is not None:
        def _pump():
            rt.pump()
            try:
                root.after(30, _pump)
            except tk.TclError:
                pass
        root.after(30, _pump)
        root.bind('<Destroy>', lambda e: scope.destroy() if e.widget is root else None)
    if fonts:
        print("  FONT rows=%d  FONTREF applied to %d widget(s)" % (len(fonts), len(applied)))
    for nt in notes:
        print("  " + nt)
    return (root, made, rt) if rt is not None else (root, made)


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
