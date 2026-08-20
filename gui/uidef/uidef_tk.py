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
from uidef import doc_source as uidef_doc_source

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
    # R66. ttk supplies a Treeview, which is BOTH a grid (columns, show='headings')
    # and a tree (show='tree'), so four of the five are native here too.
    'grid', 'tree', 'detail', 'summary', 'statusbar',
))
FRAME_KINDS = frozenset(('grid', 'tree', 'detail', 'summary', 'statusbar'))
FLOWS_SUPPORTED = frozenset(('row', 'column', 'grid', 'free'))
DISPATCH_SUPPORTED = frozenset(('ui', 'worker', 'host'))
DATA_SIZED    = {'text','list','combo','image'}

KIND_WIDGET = {          # contract section 4, the fourteen v1 kinds
    'form':'toplevel', 'panel':'frame', 'group':'labelframe',
    'pageset':'notebook', 'page':'frame',
    'label':'Label', 'text':'Entry', 'button':'Button', 'check':'Checkbutton',
    'radio':'Radiobutton', 'list':'Listbox', 'combo':'Combobox', 'image':'Label',
    'menu':'menu',
    # R66, contract 4b.
    'grid':'Treeview', 'tree':'Treeview', 'detail':'Frame', 'summary':'Frame',
    'statusbar':'Label',
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


def source_of(path):
    """The DOC's declared work areas and relation edges. R66, contract 4b(a).

    Separate from `load` on purpose: `load` returns three things and two other
    tools unpack exactly three. Widening it to carry this broke `dispatch_test.py`
    and `uidef_tk_menu.py` the moment it was tried, which is the same class of
    mistake as R22.1 -- a shared helper is a contract, and changing its shape is a
    change to every caller whether or not you looked at them.
    """
    return uidef_doc_source(list(Dbf(path).rows()))


def tree(objs):
    kids = {}
    for r in objs:
        kids.setdefault((r['PARENT'] or '').strip(), []).append(r)
    for k in kids:
        kids[k].sort(key=lambda r: int((r['ORDINAL'] or '0').strip() or 0))
    return kids


def describe(path):
    doc, fonts, objs = load(path)
    src_aliases, src_rels = source_of(path)
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


def frame_widget(parent, kind, r, pr, cap, src_aliases, src_rels):
    """R66/contract 4b -- the five ERSATZ regions on ttk.

    Structure, not data: a design-time preview has no records, which is the same
    choice `text` makes when it renders an empty Entry. A grid's columns come from
    its BINDING (contract 10c) and a tree's edges from SOURCE (4b(a)), so nothing
    here is generated from a count property -- which is what R6 refused and what
    contract 4 now records as answered rather than overruled.
    """
    from tkinter import ttk
    b = (r['BINDING'] or '').strip()
    specs = [x.strip() for x in b.split(',') if x.strip()]
    first = (src_aliases[0] if src_aliases else '?')

    def heads():
        out = []
        for sp in specs:
            if sp == '*':
                out.append(first.upper() + '.*')
            elif sp.endswith('.*'):
                out.append(sp.upper())
            else:
                out.append(sp.split('.')[-1].upper())
        return out or ['*']

    if kind == 'grid':
        cols = heads()
        try:
            n = max(1, min(int(float(pr.get('rowlimit', 3) or 3)), 5))
        except ValueError:
            n = 3
        w = ttk.Treeview(parent, columns=cols, show='headings', height=n)
        for c in cols:
            w.heading(c, text=c)
            w.column(c, width=90, stretch=False)
        return w
    if kind == 'tree':
        root = b.lower() or first
        w = ttk.Treeview(parent, show='tree', height=max(2, 1 + len(src_rels)))
        top = w.insert('', 'end', text=root.upper(), open=True)
        edges = [(c, e) for a_, c, e in src_rels if a_ == root]
        for c, e in edges:
            w.insert(top, 'end', text='%s   ON %s' % (c.upper(), e or '?'))
        if not edges:
            w.insert(top, 'end', text='(no Relation edge in SOURCE)')
        return w
    if kind in ('detail', 'summary'):
        w = ttk.Frame(parent, relief='groove', borderwidth=1)
        if kind == 'detail':
            if any(sp.endswith('.*') or sp == '*' for sp in specs):
                names = ['(every field of %s)' % first.upper()]
            else:
                names = heads()
            lines = ['%s :' % nm for nm in names]
        else:
            root = b.lower() or first
            kidsx = [c for a_, c, _e in src_rels if a_ == root]
            lines = (['%s : n' % c.upper() for c in kidsx]
                     or ['(no child of %s in SOURCE)' % root.upper()])
        for ln in lines:
            ttk.Label(w, text=ln).pack(anchor='w')
        return w
    # statusbar -- 4b(c): reports, does not compute; an unsupplied value is omitted.
    labels = {'rows': 'ROWS SHOWN', 'limit': 'LIMIT', 'order': 'ORDER',
              'root': 'ROOT', 'recno': 'RECNO', 'status': 'STATUS'}
    shows = [x.strip().lower()
             for x in str(pr.get('shows', '')).replace(',', ' ').split()]
    txt = ' | '.join('%s: --' % labels[x] for x in shows if x in labels)
    return ttk.Label(parent, relief='sunken', anchor='w',
                     text=txt or '(statusbar declares no Shows)')


def build_window(path, registry=None, host=None):
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font as tkfont
    doc, fonts, objs = load(path)
    src_aliases, src_rels = source_of(path)
    kids = tree(objs)
    rec = {(r['OBJID'] or '').strip(): r for r in objs}

    # R37: the reference consumer uses the shared runtime rather than wiring
    # handlers itself. The lock domains come from the document's own SOURCE (R36),
    # so this backend never decides what to serialize against -- it is told.
    rt = scope = None
    scopes = {}
    if registry is not None:
        import uidef_runtime as _urt
        rt = _urt.Runtime(_urt.domains_from_source(doc['SOURCE']), registry, host=host)
        scope = _urt.Scope('window')

    CONTAINER_KINDS = ('form', 'panel', 'group', 'page', 'pageset')

    def scope_for(oid):
        """R21.4 says a CONTAINER's destruction cancels the work its handlers
        queued. R38 gave the whole window one scope, which cancels a sibling's work
        when any container goes -- correct for a window and wrong for a container,
        against a rule this lane wrote itself. One scope per container, and a
        handler uses its nearest enclosing one."""
        cur = oid
        while cur:
            if cur in scopes:
                return scopes[cur]
            cur = (rec[cur]['PARENT'] or '').strip() if cur in rec else ''
        return scope
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
            # R56: emphasis is part of the font's identity, not a decoration on it.
            fontobj[i] = tkfont.Font(
                family=fam, size=size,
                weight='bold' if (fp.get('bold') or '').upper().startswith('.T') else 'normal',
                slant='italic' if (fp.get('italic') or '').upper().startswith('.T') else 'roman')
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
            if kind in FRAME_KINDS:
                w = frame_widget(parent, kind, r, pr, cap, src_aliases, src_rels)
            else:
                w = None
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
            if w is None and factory is None:
                print("REFUSED kind %r on %s -- contract s4" % (kind, oid))
                continue
            assert kind in KINDS_RENDERED, (
                "%r renders but is not in KINDS_RENDERED -- the constant has drifted"
                % kind)
            if w is None:
                w = factory()
            if rt is not None and kind in CONTAINER_KINDS:
                import uidef_runtime as _urt2
                sc = _urt2.Scope(oid)
                scopes[oid] = sc
                # Destroying THIS container cancels only what THIS container queued.
                w.bind('<Destroy>',
                       (lambda e, s_=sc, w_=w: s_.destroy() if e.widget is w_ else None),
                       add='+')
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
                    own = scope_for((r['PARENT'] or '').strip())
                    try:
                        w.configure(command=(lambda n=name, d=disp, a=alias, c=comp,
                                             s_=own: rt.fire(n, d, s_, alias=a,
                                                             completion=c)))
                    except tk.TclError:
                        pass                      # not a command widget
            made[oid] = w
            build(oid, w)

    build("", root)
    if rt is not None:
        # The pump reschedules itself, so at teardown there is always exactly one
        # `after` in flight. Letting it fire into a torn-down interpreter prints
        # `invalid command name "..._pump"` from Tcl -- on stderr, from a callback,
        # with no traceback into this file. Harmless, and it is noise in every
        # evidence capture this lane produces. Cancel it with the window.
        pump_id = [None]

        def _pump():
            rt.pump()
            try:
                pump_id[0] = root.after(30, _pump)
            except tk.TclError:
                pump_id[0] = None
        pump_id[0] = root.after(30, _pump)

        def _root_gone(e):
            if e.widget is not root:
                return
            if pump_id[0] is not None:
                try:
                    root.after_cancel(pump_id[0])
                except tk.TclError:
                    pass
                pump_id[0] = None
            scope.destroy()
        root.bind('<Destroy>', _root_gone)
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
