#!/usr/bin/env python3
"""What a UIDEF document REQUIRES, and whether a given target can meet it.

AIF-120. R22's open item, stated there as:

    The refusal report is per-render, not per-document. A target cannot ask
    "will this menu work here?" without building it.

Three rulings this lane has now reached the same conclusion from -- R7 (an unbound
control must not render as an ordinary empty box), R22.4 (an item whose capability
is absent must not render as an ordinary live item), R23.2 (a container whose layout
is unspecified must not render as an ordinary stack) -- are all refusals discovered
while building a window. That is late. A generator author wants the answer before
there is a window, from the table alone.

So: read a document, list what it requires, compare that against what a target
declares, and print exactly what will be refused. The target profiles are IMPORTED
from the targets themselves, never restated here -- restating a fact that already
exists somewhere is the mistake R22.1 and R23.4 both landed on.
"""
import os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef                                    # doc_alias_tables (R66)
import workspace                                # R83, the DTSHEMA reader
import resolve_workspace                        # R84, which file that name wins
# `read_vfp_binary` is the VFP binary reader and it lives in tools/vfp.
# gui/uidef/read_vfp_binary.py is a GITIGNORED working copy, so importing it
# from this directory made nine committed tools unimportable on a fresh clone --
# found by the house 'sweep for your own leftovers' rule, not by anything failing.
# tools/vfp goes on the path FIRST so the ignored copy can never shadow it.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vfp'))
from read_vfp_binary import Dbf


def parse_props(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if ' = ' in line:
            k, v = line.split(' = ', 1)
            out[k.strip().lower()] = v.strip().strip('"')
    return out


def parse_handlers(txt):
    """`Event = Name / dispatch [-> Completion]` -- contract section 9."""
    out = []
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if '=' not in line:
            continue
        ev, rest = line.split('=', 1)
        comp = None
        if '->' in rest:
            rest, comp = rest.split('->', 1)
            comp = comp.strip()
        parts = [p.strip() for p in rest.split('/')]
        out.append((ev.strip(), parts[0], (parts[1] if len(parts) > 1 else 'ui').lower(), comp))
    return out


# R17: a BOUND control's width lives in the data schema, not in the design.
# px = 7.00 * chars + 11.4, fitted on STUDENTS (r=0.9982) and ACCOUNTS (r=0.9977).
R17_SLOPE, R17_INTERCEPT = 7.00, 11.4

# R25: the width follows the INPUT MASK, not the field. Same intercept for both
# mask classes; the slope is the per-character advance, and a digit is narrower
# than an X in the fonts these forms use.
#   X masks     : 7.00 * len + 10   -- exact on 6 of 6 at length >= 15
#   digit masks : 6.43 * len + 10   -- fitted on 4 points, not exact
# A type with no mask is a constant: date 62 px (3 of 3), logical 18 px (1 of 1).
MASK_SLOPE = {'X': 7.00, '9': 6.43}
MASK_INTERCEPT = 10.0
UNMASKED_PX = {'D': 62.0, 'L': 18.0}


def mask_width(mask, ftype):
    """Predicted px from the mask, or from the type when there is no mask."""
    m = (mask or '').strip().strip('"')
    if not m:
        return UNMASKED_PX.get(ftype)
    cls = 'X' if m.upper().count('X') >= len(m) / 2.0 else '9'
    return MASK_SLOPE[cls] * len(m) + MASK_INTERCEPT

# A control kind implies what it can bind to. This is the loosest defensible
# reading -- a `check` needs a logical, and everything else takes text.
KIND_WANTS = {'check': set('L'), 'radio': set('L')}

# R66. The five data-frame kinds, measured from ERSATZ (R65). They divide three ways
# by what BINDING means on them, which is why a single alias.field rule could not
# cover them: a control binds a FIELD, a frame binds a ROW or a ROOT.
SPEC_KINDS   = {'grid', 'detail'}        # BINDING is a tuple spec -- section 10c
ROOT_KINDS   = {'tree', 'summary'}       # BINDING is a bare alias: the root
# R85. A splitter is two panes and a boundary the user drags. Arity is a KIND
# rule here rather than a property-conditional one, which is the whole reason
# it is a KIND: `splitter` with three children is refusable, `panel` with a
# `Sash` flag and three children is a question nobody can answer.
def weight_of(pr):
    """R79's Weight, read the same way all four backends read it. R85.

    This is the FIFTH copy of six lines -- uidef_wx, uidef_tk, uidef_html and
    uidef_text each carry their own, and now the checker needs one. That is a
    smell and it is recorded rather than smoothed: a property whose meaning
    lives in five places can mean five things, and the only reason it does not
    yet is that all five were written the same afternoon. Naming it here so the
    consolidation is a known unit and not a surprise.
    """
    v = str(pr.get('weight', '')).strip()
    if not v:
        return 0
    try:
        n = int(float(v))
    except ValueError:
        return 0
    return n if n > 0 else 0


SPLITTER_KIND = 'splitter'
SPLITTER_PANES = 2
UNBOUND_KIND = 'statusbar'               # BINDING must be empty
FRAME_KINDS  = SPEC_KINDS | ROOT_KINDS | {UNBOUND_KIND}
# BETA-7.1: the shipped browse is read-only, editing explicitly disabled. Contract
# 4b(b) refuses a document that says otherwise rather than ignoring it.
READONLY_KINDS = SPEC_KINDS
FALSEY = {'false', '.f.', 'f', '0', 'no', 'off'}
# Contract 4b(c): a statusbar renders TupleStream::status_line(); Shows filters what
# that reports rather than naming values the reader computes.
STATUS_SHOWS = {'rows', 'limit', 'order', 'root', 'recno', 'status'}
# Contract 4c. Each of these names a DbTupleStream method, so their legal values are
# the engine's, not a taste.
# R73. Was {'physical','inx','cnx'} -- three values, because DbTupleStream has
# three setters. Measured: set_order_inx() (db_tuple_stream.cpp:547) and
# set_order_cnx() (:553) are BYTE-IDENTICAL, both setting NavMode::OrderVector
# and nothing else, and neither attaches an index or selects a tag. The engine
# picks the format from the table itself -- WORKSPACE OPEN's own usage says
# "indexes are chosen by DBF flavor: true x64/v128 CDX, classic VFP/v32 CNX".
# So a document naming `inx` or `cnx` purports to choose something the engine
# derived from the file. There are TWO modes, not three.
STREAM_ORDERS = {'physical', 'ordered'}
# Kept working, because the corpus and P2_order_ok already say `cnx` and a
# vocabulary change should not invalidate documents that were correct when
# written. Accepted, mapped to `ordered`, and reported -- not silently equated.
DEPRECATED_ORDERS = {'inx': 'ordered', 'cnx': 'ordered'}
ROWLIMIT_MAX = 200                           # app_smart_browser.cpp clamps 1..200


def schema_of(dbf_path):
    t = Dbf(dbf_path)
    return {name.lower(): (typ, width, dec) for name, typ, width, dec in t.fields}


def lock_domains(relations, aliases):
    """R26: the unit of serialization is the transitive closure of related areas.

    Returns a list of sets. A handler that locks only the areas it names is not
    serialized, because navigating any area in a domain repositions the others
    without passing through their interfaces -- measured at 100/100 wrong in
    `relate_test.py`. A target needs this BEFORE it dispatches anything, and it can
    only get it from the document.
    """
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a_, b_, _expr in relations:
        union(a_, b_)
    for al in aliases:
        find(al)
    groups = {}
    for x in parent:
        groups.setdefault(find(x), set()).add(x)
    return sorted(groups.values(), key=lambda g: (-len(g), sorted(g)))


def stream_refusals(m, doms=None):
    """R70. Which grids in this document may NOT be bound to a DbTupleStream.

    Exists because the wx generator's `--stream` mode emitted a live binding for
    every grid, including the three the contract already refuses -- an editable
    grid (4b(b)), an ordinal spec (10c/R65.3), and a two-alias spec with no
    Relation edge (10c). A generator that ignores the gate its own document failed
    is worse than no gate: the refusal is printed and the binding ships anyway.

    Schema-free by construction. Every reason below is a property of the DOCUMENT,
    so this answers with no tables supplied -- which matters because the generator
    is normally run without any. Schema-dependent refusals stay in bind_check.

    Returns {objid: reason}. A grid absent from the mapping is bindable.
    """
    out = {}
    if doms is None:
        doms = lock_domains(m['relations'], m['aliases']) if m['relations'] else []

    def refuse(oid, why):
        out.setdefault(oid, why)

    for oid, kind, b, pr in m['frames']:
        if kind != 'grid':
            continue
        if str(pr.get('readonly', '')).strip().lower() in FALSEY:
            refuse(oid, 'ReadOnly is false -- contract 4b(b) refuses an editable '
                        'row path (BETA-7.1)')
            continue
        o = str(pr.get('order', '')).strip().lower()
        if o and o not in STREAM_ORDERS and o not in DEPRECATED_ORDERS:
            refuse(oid, 'Order=%s is not one of %s -- contract 4c'
                        % (o, ', '.join(sorted(STREAM_ORDERS))))
            continue
        rl = str(pr.get('rowlimit', '')).strip()
        if rl:
            try:
                n = int(float(rl))
            except ValueError:
                n = 0
            if n < 1:
                refuse(oid, 'RowLimit=%s is not a positive integer; it is '
                            'next_page(max_rows) -- contract 4c' % rl)
                continue
        specs = [x.strip() for x in (b or '').split(',') if x.strip()]
        if not specs:
            refuse(oid, 'no BINDING; a grid without a spec has no row to stream')
            continue
        bad = [sp for sp in specs if sp.startswith('#')]
        if bad:
            refuse(oid, 'ordinal spec %s is unreachable through the shell '
                        '(AIF-037 cuts # to end of line) -- contract 10c'
                        % ', '.join(bad))
            continue
        named = sorted({sp.split('.')[0].lower() for sp in specs
                        if sp != '*' and '.' in sp})
        undeclared = [a for a in named if a not in m['aliases']]
        if undeclared:
            refuse(oid, 'alias %s is not declared in SOURCE'
                        % ', '.join(undeclared))
            continue
        if len(named) > 1 and not any(set(named) <= d for d in doms):
            refuse(oid, 'spec names %s and SOURCE declares no Relation joining '
                        'them -- contract 10c' % ' and '.join(named))
            continue
        if '*' in specs and not m['aliases']:
            refuse(oid, 'BINDING * has no alias in SOURCE to resolve against '
                        '-- contract 10c')
    return out


def bind_check(m, tables):
    """Join a document's BINDINGs against real DBF schemas.

    The manifest can say a document needs a data source (R24.1's REQUIRE). This
    says whether a PARTICULAR source satisfies it, which is the join R17 implies:
    if a bound control's width comes from the field's declared width, then the
    schema is part of the document's meaning, not an external detail.
    """
    out = []
    for alias, tbl in sorted(m['aliases'].items()):
        if alias not in tables:
            out.append(('REFUSE', 'alias %s -> %s' % (alias, tbl),
                        'no schema supplied for this table'))
    widths = []
    # R53, measured over the 170-form corpus: 159 ControlSource occurrences,
    # 145 alias.field (91.2%), 8 empty, 4 object references, 2 bare field. The
    # three minorities are three DIFFERENT things and were not being told apart.
    first_alias = next(iter(m['aliases']), None)
    doms = lock_domains(m['relations'], m['aliases']) if m['relations'] else []
    for oid, kind, binding, org_w, mask in m['bound']:
        # R66/contract 4b + 10c. BINDING means three different things now, and which
        # one it means is a property of the KIND, not of the string.
        if kind == UNBOUND_KIND:
            out.append(('REFUSE', 'BINDING %s on %s' % (binding, oid),
                        'a statusbar reports the frame\'s own state and is not bound '
                        'to data -- contract 4b(c); name the values in PROPS Shows'))
            continue
        if kind in ROOT_KINDS:
            if any(c in binding for c in '.,*'):
                out.append(('REFUSE', 'BINDING %s on %s' % (binding, oid),
                            '%s binds the ROOT alias, not a field or a spec -- its '
                            'shape is the SOURCE relation graph (contract 4b(a))'
                            % kind))
            elif binding not in m['aliases']:
                out.append(('REFUSE', 'BINDING %s on %s' % (binding, oid),
                            'alias %s is not declared in SOURCE' % binding))
            continue
        if kind not in SPEC_KINDS and (',' in binding or '*' in binding):
            out.append(('REFUSE', 'BINDING %s on %s' % (binding, oid),
                        'a tuple spec binds a ROW; a %s binds one field -- '
                        'contract 10c' % kind))
            continue
        specs = [x.strip() for x in binding.split(',')] if kind in SPEC_KINDS \
                else [binding]
        used = []
        for spec in specs:
            if spec.startswith('#'):
                # R65.3. Not "bad binding" -- a form BETA-4.4 declares and the
                # AIF-037 lexer deletes before the spec parser ever sees it.
                out.append(('REFUSE', 'BINDING %s on %s' % (spec, oid),
                            'ordinal spec is unreachable through the shell '
                            '(AIF-037 cuts # to end of line); name the field'))
                continue
            parts = spec.split('.')
            head = parts[0].lower()
            if len(parts) > 2 or head in ('this', 'thisform', 'thisformset'):
                # `This.Parent.SysTray1.Tiptext` -- a control bound to another
                # CONTROL'S PROPERTY, not to data. Not a malformed alias.field; a
                # different kind of thing, which UIDEF v1 does not model. It used to
                # fall through to the alias lookup, miss, and be skipped in SILENCE.
                out.append(('REFUSE', 'BINDING %s on %s' % (spec, oid),
                            'object reference, not a data binding -- outside v1'))
                continue
            if spec == '*':
                # Contract 10c: the FIRST alias in SOURCE, never "the current work
                # area" -- section 10 refuses ambient resolution and this is the
                # third place the same rule applies.
                if first_alias is None:
                    out.append(('REFUSE', 'BINDING * on %s' % oid,
                                'no alias is declared in SOURCE for * to resolve '
                                'against'))
                    continue
                sch = tables.get(first_alias)
                if sch is None:
                    out.append(('REFUSE', 'BINDING * on %s' % oid,
                                'no schema supplied for alias %s' % first_alias))
                    continue
                used.extend((first_alias, f) for f in sch)
                continue
            if len(parts) == 1:
                # A bare field name resolves against whatever work area happens to be
                # current -- the ambient state section 10 already forbids for `Table`.
                out.append(('REFUSE', 'BINDING %s on %s' % (spec, oid),
                            'bare field name; not alias.field, and the current work '
                            'area is ambient state'))
                continue
            alias, field = parts[0], parts[1]
            sch = tables.get(alias.lower())
            if sch is None:
                out.append(('REFUSE', 'BINDING %s on %s' % (spec, oid),
                            'alias %s is not declared in SOURCE' % alias))
                continue
            if field == '*':
                used.extend((alias.lower(), f) for f in sch)
                continue
            f = sch.get(field.lower())
            if f is None:
                out.append(('REFUSE', 'BINDING %s on %s' % (spec, oid),
                            'field not in the schema'))
                continue
            typ, width, dec = f
            want = KIND_WANTS.get(kind)
            if want and typ not in want:
                out.append(('REFUSE', '%s %s bound to %s' % (kind, oid, spec),
                            'field type %s cannot drive a %s' % (typ, kind)))
                continue
            used.append((alias.lower(), field.lower()))
            if org_w and kind not in FRAME_KINDS:
                px = R17_SLOPE * width + R17_INTERCEPT      # R17, from the field
                mx = mask_width(mask, typ)                  # R25, from the mask
                widths.append((oid, spec, width, px, mx, org_w))
        # Contract 10c: a spec across two aliases describes a JOIN, so SOURCE must
        # already relate them -- otherwise the row is invented and R26's lock domain
        # does not cover it.
        named = sorted({a for a, _ in used})
        if len(named) > 1 and not any(set(named) <= d for d in doms):
            out.append(('REFUSE', 'BINDING %s on %s' % (binding, oid),
                        'spec names %s, and SOURCE declares no Relation joining '
                        'them -- contract 10c' % ' and '.join(named)))
    if widths:
        e17 = [abs(px - ow) for _, _, _, px, _, ow in widths]
        e25 = [abs(mx - ow) for _, _, _, _, mx, ow in widths if mx is not None]
        out.append(('NOTE', 'width check on %d bound control(s)' % len(widths),
                    'R17 from the field: mean |err| %.1f px, max %.1f  |  '
                    'R25 from the mask: mean |err| %.1f px, max %.1f (n=%d)'
                    % (sum(e17) / len(e17), max(e17),
                       (sum(e25) / len(e25)) if e25 else -1,
                       max(e25) if e25 else -1, len(e25))))
    return out, widths


def manifest(path):
    rows = list(Dbf(path).rows())
    objs = [r for r in rows if (r['RECKIND'] or '').strip() == 'OBJ']
    fontrows = [r for r in rows if (r['RECKIND'] or '').strip() == 'FONT']
    rec = {(r['OBJID'] or '').strip(): r for r in objs}
    children = collections.defaultdict(list)
    for r in objs:
        children[(r['PARENT'] or '').strip()].append(r)

    m = {
        'document': os.path.basename(path),
        'objects': len(objs),
        'kinds': collections.Counter(),
        'flows': collections.Counter(),
        'dispatch': collections.Counter(),
        'host_capabilities': set(),
        'grid_without_columns': [],
        'free_without_origin': [],
        'worker_without_completion': [],
        'spans': [],
        'bindings': 0,
        'fontrefs_out_of_range': set(),
        'fonts': 0,
        'fonts_unreferenced': [],
        'needs_origin': False,
        'tab_declared': 0,
        'tab_absent': 0,
        'aliases': {},
        'bound': [],
        'relations': [],
        'frames': [],
        'frame_with_children': [],
        'splitters': [],
        # R79. Weight/Fill belong to any child of a flowed container, not only to
        # frame kinds, so the checker needs every object's PROPS -- not just the
        # subsets the earlier rulings happened to collect.
        'all_props': [],
    }
    for r in rows:
        if (r['RECKIND'] or '').strip() == 'DOC':
            # R66. This was `parse_props(r['SOURCE'])['alias']`, and parse_props
            # returns a DICT -- so a SOURCE declaring four work areas kept only the
            # LAST one, in the field whose entire purpose is to declare several.
            # R26's lock domains survived it because the Relation edges carry the
            # closure, but `alias not declared in SOURCE` could not fire and
            # contract 10c's "first alias" had no first.
            m['aliases'].update(uidef.doc_alias_tables([r]))
            for line in (r['SOURCE'] or '').replace('\r\n', '\n').split('\n'):
                if not line.lower().startswith('relation = '):
                    continue
                body = line.split(' = ', 1)[1]
                expr = ''
                if ' ON ' in body:
                    body, expr = body.split(' ON ', 1)
                if ' -> ' in body:
                    a_, b_ = body.split(' -> ', 1)
                    m['relations'].append((a_.strip().lower(), b_.strip().lower(),
                                           expr.strip()))
    referenced = set()
    for r in objs:
        oid = (r['OBJID'] or '').strip()
        kind = (r['KIND'] or '').strip().lower()
        pr_all = parse_props(r['PROPS'])
        m['all_props'].append((oid, kind, pr_all))
        flow = (r['FLOW'] or '').strip().lower()
        m['kinds'][kind] += 1
        if flow:
            m['flows'][flow] += 1
            pr = parse_props(r['PROPS'])
            if flow == 'grid' and 'columns' not in pr:
                m['grid_without_columns'].append(oid)
            if flow == 'free':
                kids = children.get(oid, [])
                if kids and not any((c['ORIGIN'] or '').strip() for c in kids):
                    m['free_without_origin'].append(oid)
        if (r['ORIGIN'] or '').strip():
            m['needs_origin'] = True
        if kind not in ('form',):
            t = str(r['TABORDINAL'] or '').strip()
            if t and t != '0':
                m['tab_declared'] += 1
            else:
                m['tab_absent'] += 1
        span = (r['SPAN'] or '').strip()
        if span and span not in ('0', '1'):
            m['spans'].append((oid, span))
        b = (r['BINDING'] or '').strip()
        if b:
            m['bindings'] += 1
            ow = parse_props(r['ORIGIN']).get('origin_width')
            try:
                ow = float(ow) if ow else None
            except ValueError:
                ow = None
            m['bound'].append((oid, kind, b.lower(), ow,
                               parse_props(r['PROPS']).get('mask')))
        if kind in FRAME_KINDS:
            m['frames'].append((oid, kind, b, parse_props(r['PROPS'])))
        # Contract field table: FONTREF is "1-based index into this document's FONT
        # rows. 0 = target default." An index, not an OBJID -- the first version of
        # this check compared it to FONT-row OBJIDs and reported a false defect on
        # every imported form in the lane.
        fr = (r['FONTREF'] or '').strip()
        try:
            fri = int(float(fr or 0))
        except ValueError:
            fri = -1
        if fri < 0 or fri > len(fontrows):
            m['fontrefs_out_of_range'].add(fr)
        elif fri > 0:
            referenced.add(fri)
        for ev, name, disp, comp in parse_handlers(r['HANDLERS']):
            m['dispatch'][disp] += 1
            if disp == 'host':
                m['host_capabilities'].add(name)
            if disp == 'worker' and not comp:
                m['worker_without_completion'].append((oid, name))
    m['fonts'] = len(fontrows)
    m['fonts_unreferenced'] = [i for i in range(1, len(fontrows) + 1)
                               if i not in referenced]
    # R66/contract 4b(a): a tree or a summary takes its shape from the SOURCE
    # relation graph, which the document already states once. Child rows would be a
    # second copy of the closure that can drift from the first.
    for oid, kind, _b, _pr in m['frames']:
        if kind in ROOT_KINDS and children.get(oid):
            m['frame_with_children'].append((oid, kind, len(children[oid])))
    # R85. Collected with each pane's Weight, because on a splitter Weight is not
    # a share of slack -- it IS the sash gravity, w1/(w1+w2). Same property, and
    # the container it sits in decides what it means.
    #
    # (That formula was written w2/(w1+w2) here for one afternoon, from memory.
    # It is measured: under Xvfb, gravity 0.0 leaves the FIRST pane at its size
    # and gives the growth to the second; 1.0 gives it to the first. So gravity
    # is the first pane's share, and w1 belongs on top.)
    #
    # R85.1 also needs the PARENT's kind, because "does this splitter fill its
    # parent" has two different answers: a splitter in a sizer fills only if it
    # says Weight/Fill, but a splitter that is itself a PANE of another splitter
    # always fills -- Split*() gives a pane the whole side, there is no
    # proportion to state. Same object, and the container decides. Again.
    kind_of = {(r['OBJID'] or '').strip(): (r['KIND'] or '').strip().lower()
               for r in rows if (r['RECKIND'] or '').strip() == 'OBJ'}
    for r in rows:
        if (r['RECKIND'] or '').strip() != 'OBJ':
            continue
        if (r['KIND'] or '').strip().lower() != SPLITTER_KIND:
            continue
        oid = (r['OBJID'] or '').strip()
        kids = children.get(oid, [])
        pr = parse_props(r['PROPS'])
        m['splitters'].append((oid, (r['FLOW'] or '').strip().lower(),
                               [(c, weight_of(parse_props(c['PROPS']))) for c in kids],
                               pr, (r['ORIGIN'] or '').strip(),
                               kind_of.get((r['PARENT'] or '').strip(), '')))
    return m


# -- target profiles.  IMPORTED from the target, or declared as a hypothetical. ---

def profile_tk():
    import uidef_tk, uidef_tk_host                      # needs tkinter (py3.12 here)
    return {
        'name': 'tk -- uidef_tk.py + uidef_tk_host.py',
        'kinds': set(uidef_tk.KINDS_RENDERED),
        'flows': set(uidef_tk.FLOWS_SUPPORTED),
        'dispatch': set(uidef_tk.DISPATCH_SUPPORTED),
        'host': set(uidef_tk_host.CAPABILITIES),
        'span': True,
        'origin': True,
    }


def profile_text():
    """The third backend (R35): a character grid, no fonts, no pixels."""
    import uidef_text
    return {
        'name': 'text -- uidef_text.py (character cells, no fonts)',
        'kinds': set(uidef_text.KINDS_RENDERED),
        'flows': set(uidef_text.FLOWS_SUPPORTED),
        'dispatch': set(uidef_text.DISPATCH_SUPPORTED),
        'host': set(uidef_text.CAPABILITIES),
        'span': True,
        'origin': True,
    }


def profile_html():
    """The second REAL backend (R34). Imported, never restated."""
    import uidef_html
    return {
        'name': 'html -- uidef_html.py (flexbox / CSS grid)',
        'kinds': set(uidef_html.KINDS_RENDERED),
        'flows': set(uidef_html.FLOWS_SUPPORTED),
        'dispatch': set(uidef_html.DISPATCH_SUPPORTED),
        'host': set(uidef_html.CAPABILITIES),
        'span': True,
        'origin': True,
    }


# A deliberately small target, to show the check working against something that is
# not the reference consumer. Nothing implements this; it is a profile, not a claim.
PROFILE_MINIMAL = {
    'name': 'minimal -- labels, fields and buttons, stacked, synchronous',
    'kinds': {'form', 'label', 'text', 'button'},
    'flows': {'column', 'free'},
    'dispatch': {'ui'},
    'host': set(),
    'span': False,
    'origin': False,
}


def check(m, p):
    """Return a list of (severity, subject, reason). REFUSE stops a render."""
    out = []
    for k, n in sorted(m['kinds'].items()):
        if k and k not in p['kinds']:
            out.append(('REFUSE', 'kind %s (x%d)' % (k, n),
                        'target does not render this kind -- contract s4'))
    for f, n in sorted(m['flows'].items()):
        if f not in p['flows']:
            out.append(('REFUSE', 'FLOW %s (x%d)' % (f, n),
                        'target does not implement this flow -- contract s5'))
    for d, n in sorted(m['dispatch'].items()):
        if d not in p['dispatch']:
            out.append(('REFUSE', 'DISPATCH %s (x%d)' % (d, n),
                        'target does not implement this dispatch value -- R11, R20'))
    for c in sorted(m['host_capabilities']):
        if c not in p['host']:
            out.append(('REFUSE', 'capability %s' % c,
                        'target does not provide this host capability -- R20, R22.4'))
    for oid in m['grid_without_columns']:
        out.append(('REFUSE', 'grid container %s' % oid,
                    'FLOW=grid with no Columns property -- R23.2'))
    for oid, name in m['worker_without_completion']:
        out.append(('REFUSE', 'handler %s on %s' % (name, oid),
                    'DISPATCH=worker with no ON_COMPLETE -- R11.3'))
    for fr in sorted(m['fontrefs_out_of_range']):
        out.append(('REFUSE', 'FONTREF %s' % fr,
                    'not a 1-based index into this document\'s %d FONT row(s)'
                    % m['fonts']))
    if m['fonts_unreferenced']:
        out.append(('NOTE', 'FONT row(s) %s unreferenced'
                    % ','.join(str(i) for i in m['fonts_unreferenced']),
                    'carried as source metrics; no object selects them'))
    if m['spans'] and not p['span']:
        out.append(('REFUSE', 'SPAN on %d object(s)' % len(m['spans']),
                    'target does not implement SPAN -- contract s5'))
    if m['needs_origin'] and not p['origin']:
        out.append(('DEGRADE', 'ORIGIN present', 'target ignores ORIGIN; layout falls '
                    'back to ORDINAL, which R16 says is often correct anyway'))
    for oid in m['free_without_origin']:
        out.append(('DERIVE', 'container %s' % oid,
                    'FLOW=free with no ORIGIN on any child -- position derived from '
                    'ORDINAL and must be declared (R12.3, R23.3)'))
    if m['relations']:
        doms = lock_domains(m['relations'], m['aliases'])
        multi = [d for d in doms if len(d) > 1]
        for d in multi:
            out.append(('REQUIRE', 'lock domain {%s}' % ', '.join(sorted(d)),
                        'R26: these work areas move together, so a mutating handler '
                        'must serialize against the whole set, not the area it names'))
    elif m['aliases'] and len(m['aliases']) > 1:
        out.append(('NOTE', '%d work areas, no relations declared' % len(m['aliases']),
                    'each is its own lock domain -- or the document did not say '
                    '(R26.2)'))
    if m['tab_absent'] and not m['tab_declared']:
        out.append(('DERIVE', '%d control(s) with no TABORDINAL' % m['tab_absent'],
                    'tab order must be derived and declared; measured, a derived '
                    'order matches the document exactly in 25.7% of groups'))
    elif m['tab_absent'] and m['tab_declared']:
        out.append(('DERIVE', '%d of %d control(s) lack TABORDINAL'
                    % (m['tab_absent'], m['tab_absent'] + m['tab_declared']),
                    'a partial tab order is the worst case: the gaps must be '
                    'derived and interleaved with the declared stops'))
    # R79. Weight and Fill are per-child layout properties and are checked on
    # EVERY object, not just frames -- any child of a flowed container may carry
    # them. Absent means 0/false, which is what every document said before they
    # existed, so silence is never a finding.
    for oid, kind, pr in m.get('all_props', []):
        w = str(pr.get('weight', '')).strip()
        if w:
            try:
                n = int(float(w))
            except ValueError:
                n = -1
            if n < 0:
                out.append(('REFUSE', '%s %s Weight=%s' % (kind, oid, w),
                            'Weight is a share of the FLOW axis and must be a '
                            'non-negative integer; 0 means fixed -- contract 5c'))
        f = str(pr.get('fill', '')).strip().lower()
        if f and f not in FALSEY and f not in ('true', '.t.', 't', '1', 'yes', 'on'):
            out.append(('REFUSE', '%s %s Fill=%s' % (kind, oid, f),
                        'Fill is a boolean -- it says whether the child stretches '
                        'ACROSS the flow axis, contract 5c'))

    # R66. Contract 4b. These hold with or without a schema, so they are not in
    # bind_check -- a document that says a grid is editable is wrong on its own.
    for oid, kind, _b, pr in m['frames']:
        if kind in READONLY_KINDS:
            ro = str(pr.get('readonly', '')).strip().lower()
            if ro in FALSEY:
                out.append(('REFUSE', '%s %s ReadOnly=%s' % (kind, oid, ro),
                            'BETA-7.1 locks the shipped browse to read-only and '
                            'contract 4b(b) carries that into the kind; an editable '
                            'row path across a lock domain is not proven (R57.2)'))
        if kind == 'grid':
            # Contract 4c: these are DbTupleStream's arguments, not decoration.
            o = str(pr.get('order', '')).strip().lower()
            if o in DEPRECATED_ORDERS:
                out.append(('DEGRADE', 'grid %s Order=%s' % (oid, o),
                            'R73: `%s` names an index FORMAT, and the engine chooses '
                            'the format from the table (x64 -> CDX, classic -> CNX). '
                            'Read as `%s`. Which index and which tag are workspace '
                            'facts (DTSHEMA index=/tag=), not document facts'
                            % (o, DEPRECATED_ORDERS[o])))
            elif o and o not in STREAM_ORDERS:
                out.append(('REFUSE', 'grid %s Order=%s' % (oid, o),
                            'not an order the stream can be set to -- contract 4c '
                            'closes it to %s' % ', '.join(sorted(STREAM_ORDERS))))
            rl = str(pr.get('rowlimit', '')).strip()
            if rl:
                try:
                    n = int(float(rl))
                except ValueError:
                    n = 0
                if n < 1:
                    out.append(('REFUSE', 'grid %s RowLimit=%s' % (oid, rl),
                                'RowLimit is next_page(max_rows) and must be a '
                                'positive integer -- contract 4c'))
                elif n > ROWLIMIT_MAX:
                    out.append(('DEGRADE', 'grid %s RowLimit=%s' % (oid, rl),
                                'the house browser clamps next_page to %d '
                                '(app_smart_browser.cpp); a reader that clamps must '
                                'say so -- contract 4c' % ROWLIMIT_MAX))
            w = [x for x in str(pr.get('columnwidths', '')).split(',') if x.strip()]
            b = next((bb for oo, kk, bb, _p in m['frames'] if oo == oid), '')
            ncols = len([x for x in b.split(',') if x.strip()])
            if w and ncols and len(w) != ncols:
                out.append(('REFUSE', 'grid %s ColumnWidths has %d entr(ies)'
                            % (oid, len(w)),
                            'the spec declares %d column(s); ColumnWidths is '
                            'ordinal-aligned with it -- contract 4c' % ncols))
        if kind == UNBOUND_KIND:
            shows = [x.strip().lower()
                     for x in str(pr.get('shows', '')).replace(',', ' ').split()]
            bad = [x for x in shows if x not in STATUS_SHOWS]
            if bad:
                out.append(('REFUSE', 'statusbar %s Shows %s' % (oid, ' '.join(bad)),
                            'not a frame state value -- contract 4b(c) closes the '
                            'list to %s' % ', '.join(sorted(STATUS_SHOWS))))
            elif not shows:
                out.append(('NOTE', 'statusbar %s' % oid,
                            'no Shows property; the reader decides what to report'))
    for oid, flow, panes, pr, origin, parent_kind in m['splitters']:
        if len(panes) != SPLITTER_PANES:
            out.append(('REFUSE', 'splitter %s has %d pane(s)' % (oid, len(panes)),
                        'a splitter is exactly %d panes and the boundary between '
                        'them; wxSplitterWindow cannot hold a third and a document '
                        'that means three panes means two splitters (R85)'
                        % SPLITTER_PANES))
            continue
        if flow not in ('row', 'column'):
            out.append(('REFUSE', 'splitter %s FLOW=%s' % (oid, flow or '(none)'),
                        'FLOW is what says which way the boundary runs -- row is a '
                        'vertical sash, column a horizontal one. There is no third '
                        'answer and no default worth guessing (R85)'))
        w = [x[1] for x in panes]
        if sum(w) == 0:
            out.append(('NOTE', 'splitter %s' % oid,
                        'neither pane declares Weight, so the sash gravity is 0.0 -- '
                        'the first pane holds its size and the second absorbs the '
                        'resize. That is wx\'s default and all three measured '
                        'splitters run at it, but it is now stated rather than '
                        'inherited (R85)'))
        mp = str(pr.get('minpane', '')).strip()
        if mp:
            try:
                n = int(float(mp))
            except ValueError:
                out.append(('REFUSE', 'splitter %s MinPane=%s' % (oid, mp),
                            'MinPane is a whole number of pixels (R85)'))
            else:
                if n < 0:
                    out.append(('REFUSE', 'splitter %s MinPane=%s' % (oid, mp),
                                'MinPane cannot be negative (R85)'))
        else:
            out.append(('NOTE', 'splitter %s' % oid,
                        'no MinPane; a pane can be dragged to nothing and the '
                        'control it holds becomes unreachable. All three measured '
                        'splitters set 120 (R85)'))
        if not origin:
            out.append(('DERIVE', 'splitter %s' % oid,
                        'no ORIGIN, so the initial boundary is the target\'s -- '
                        'wx centres it. The measured screen states 220, 500 and '
                        '260; a position is a coordinate and lives in ORIGIN under '
                        'R12, not in PROPS (R85)'))
        # R85.1. MEASURED, not reasoned. P7 was built twice from the same
        # document, changing one emitted argument:
        #
        #   Add(splitter, 0, wxALL, 6)            sash lands at 119
        #   Add(splitter, 1, wxALL|wxEXPAND, 6)   sash lands at 220
        #
        # The document said `origin_width = 220` both times. Unweighted, the
        # splitter gets its BEST size (245 px here) and wx clamps a 220 sash
        # against a 120 MinPane down to an even split -- silently. The screen
        # then contradicts the document and nothing says so.
        #
        # This is refused rather than noted because the author cannot know the
        # best size: it depends on the pane contents, the font and the platform.
        # An ORIGIN under an unweighted splitter is not wrong, it is
        # UNPREDICTABLE, and a coordinate that might mean itself is worse than
        # one that does not. R79 already gives the document the words to fix it.
        own_w = weight_of(pr)
        own_fill = str(pr.get('fill', '')).strip().lower()
        fills = bool(own_fill) and own_fill not in FALSEY
        # A pane of another splitter already fills; nothing to state and nothing
        # to lose. Measured: P8's INNER carries no proportion anywhere and its
        # own sash still lands where the document put it.
        if parent_kind == SPLITTER_KIND:
            pass
        elif not own_w and not fills:
            if origin:
                out.append(('REFUSE', 'splitter %s states ORIGIN but no Weight' % oid,
                            'an unweighted splitter is laid out at its best size, so '
                            'the sash position it names is clamped to whatever that '
                            'happens to be -- measured 220 asked, 119 rendered. Give '
                            'it Weight (and Fill across the flow) or drop the ORIGIN '
                            'and let the target centre the sash (R85.1)'))
            else:
                out.append(('NOTE', 'splitter %s has no Weight' % oid,
                            'it will be laid out at its best size rather than filling '
                            'its parent. Legal, and measured at 245 px wide for two '
                            'empty panes -- but every measured splitter in the shipped '
                            'frame is added with proportion 1 and wxEXPAND '
                            '(main_frame.cpp:703) (R85.1)'))
    for oid, kind, n in m['frame_with_children']:
        out.append(('REFUSE', '%s %s has %d child row(s)' % (kind, oid, n),
                    'a %s takes its shape from the SOURCE relations -- child rows '
                    'are a second copy of the closure (contract 4b(a))' % kind))
    if m['bindings']:
        out.append(('REQUIRE', '%d bound control(s)' % m['bindings'],
                    'target must supply a data source; widths come from the schema (R17)'))
    return out


def load_schemas(paths):
    out = {}
    for p in paths:
        alias = os.path.splitext(os.path.basename(p))[0].lower()
        out[alias] = schema_of(p)
    return out


def _find_dottalk_root():
    """Walk up for the tree that holds `dottalkpp/`. Returned rather than
    assumed: this file is run from several directories and R84's whole point is
    that a path you did not verify is a guess wearing a path's clothes."""
    d = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(d, 'dottalkpp')):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd


def source_resolution(path, ws=None):
    """Contract section 10: does every `Table` this document declares RESOLVE?

    Section 10 has said since 2026-08-19 that a document whose `Table` does not
    resolve is REFUSED, never rendered unbound -- "a width silently derived from
    a schema that was never opened is worse than no width". R82 found that
    nothing performed that refusal. This does.

    The order is the contract's own, and the second step is R82's ruling:

      1. DOCUMENT-RELATIVE. Section 10's primary rule, measured from VFP, which
         recomputes a data-source path relative to the form on every save. A
         bare name is the ZERO-DISTANCE case of that rule, not a fallback.
      2. THROUGH A DECLARED WORKSPACE, if one is supplied AND it is self-locating
         -- which per R82.3 means DTSHEMA 3, because a v2 posture resolves its
         members against `Slot::DBF` and so states which table, not where.
      3. Otherwise REFUSE.

    What this deliberately does NOT do is fall back to the environment. Reading
    `SETPATH`, `R70_DBF` or the current directory would make every document
    resolve and would report exactly the ambient-state dependency section 10
    exists to forbid. **An unresolvable Table is the honest answer** when neither
    the document nor a declared posture says where the table is.

    Returns (rows, checked) -- `checked` is False when there was nothing to
    check, so a caller can tell "no tables" from "all fine".
    """
    rows = list(Dbf(path).rows())
    tabs = uidef.doc_alias_tables(rows)
    out = []
    if not tabs:
        return out, False
    here = os.path.dirname(os.path.abspath(path))
    for alias in sorted(tabs):
        t = (tabs[alias] or '').strip()
        if not t:
            out.append(('REFUSE', 'Alias %s' % alias,
                        'declares no Table; an alias with no table is a work area '
                        'nothing can open (contract s10)'))
            continue
        cand = t if os.path.isabs(t) else os.path.join(here, t)
        if os.path.exists(cand):
            out.append(('NOTE', 'Table %s' % t,
                        'resolves document-relative (contract s10)'))
            continue
        if ws is not None and ws.self_locating:
            wc = ws.resolve_dbf(t)
            if wc and os.path.exists(wc):
                out.append(('NOTE', 'Table %s' % t,
                            'resolves through the declared workspace -> %s' % wc))
                continue
            out.append(('REFUSE', 'Table %s' % t,
                        'resolves neither beside the document nor through the '
                        'declared workspace (contract s10)'))
            continue
        why = ('does not resolve beside the document, and no self-locating '
               'workspace was supplied (contract s10)')
        if ws is not None:
            why = ('does not resolve beside the document, and the supplied '
                   'workspace is DTSHEMA %d -- it declares which table, not '
                   'where (R82.3); a v3 posture carries DBFROOT' % ws.version)
        out.append(('REFUSE', 'Table %s' % t, why))
    return out, True


def report(path, profiles, tables=None, ws=None):
    m = manifest(path)
    print("%s -- %d objects" % (m['document'], m['objects']))
    print("  kinds     : %s" % ', '.join('%s x%d' % kv for kv in sorted(m['kinds'].items()) if kv[0]))
    print("  flows     : %s" % (', '.join('%s x%d' % kv for kv in sorted(m['flows'].items())) or '(none)'))
    print("  dispatch  : %s" % (', '.join('%s x%d' % kv for kv in sorted(m['dispatch'].items())) or '(none)'))
    if m['host_capabilities']:
        print("  host caps : %d -- %s" % (len(m['host_capabilities']),
                                          ', '.join(sorted(m['host_capabilities']))))
    for p in profiles:
        res = check(m, p)
        counts = collections.Counter(s for s, _, _ in res)
        print("  vs %s" % p['name'])
        if not res:
            print("      renders with no refusals")
        for sev in ('REFUSE', 'DEGRADE', 'DERIVE', 'REQUIRE', 'NOTE'):
            for s, subj, why in res:
                if s == sev:
                    print("      %-8s %-34s %s" % (s, subj, why))
        print("      -> %s" % (', '.join('%s %d' % (k, v) for k, v in sorted(counts.items()))
                               or 'clean'))
    res10, checked10 = source_resolution(path, ws)
    print("  vs contract s10 -- does every declared Table resolve?")
    if not checked10:
        print("      the document declares no Table; nothing to resolve")
    else:
        for s_, subj, why in res10:
            print("      %-8s %-34s %s" % (s_, subj, why))
        if ws is None:
            print("      NOTE     %-34s %s"
                  % ('no workspace supplied',
                     'pass --workspace <file.dtschema> to check step 2 (R82)'))
    if tables is not None and m['bindings']:
        res, widths = bind_check(m, tables)
        print("  vs the supplied schema(s): %s" % ', '.join(sorted(tables)))
        for s_, subj, why in res:
            print("      %-8s %-34s %s" % (s_, subj, why))
        if widths:
            print("      %-10s %-22s %5s %9s %9s %9s" %
                  ('object', 'binding', 'chars', 'R17 px', 'R25 px', 'design px'))
            for oid, b, w, px, mx, ow in widths:
                print("      %-10s %-22s %5d %9.1f %9s %9.1f"
                      % (oid, b, w, px, ('%.1f' % mx) if mx is not None else '--', ow))
        if not res:
            print("      every binding resolves")
    print()
    return m


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    profs = []
    if '--minimal' in sys.argv or '--all' in sys.argv:
        profs.append(PROFILE_MINIMAL)
    if '--html' in sys.argv or '--both' in sys.argv or '--all' in sys.argv:
        profs.append(profile_html())
    if '--text' in sys.argv or '--all' in sys.argv:
        profs.append(profile_text())
    if '--minimal' not in sys.argv and '--html' not in sys.argv and '--text' not in sys.argv:
        profs.insert(0, profile_tk())
    ws = None
    if '--workspace' in sys.argv:
        i = sys.argv.index('--workspace')
        wspath = sys.argv[i + 1]
        args = [a for a in args if a != wspath]

        # R84. A workspace given by NAME is not a file until a resolver says so,
        # and this house has two resolvers that disagree. Reporting the path we
        # actually read is not decoration: three of the MCC workspace names
        # resolve to a gitignored file that shadows a tracked one, so `mcc_x64`
        # means one thing to the engine and another to anyone who cloned. This
        # lane reasoned from the tracked loser through two rulings before the
        # maintainer's own transcript exposed it.
        if os.sep not in wspath and '/' not in wspath and not os.path.isfile(wspath):
            root = os.environ.get('DOTTALK_ROOT') or _find_dottalk_root()
            if root:
                txt, rc = resolve_workspace.report(wspath, root)
                print(txt)
                if rc == 2:
                    print('  -- resolution above is ADVISORY here; this check reads '
                          'the winner, which is what the engine would read.')
                hits = [p for _, p in resolve_workspace.candidates(wspath, root)
                        if os.path.isfile(p)]
                if hits:
                    wspath = hits[0]

        ws = workspace.load(wspath)
        print('workspace %s -- DTSHEMA %d, %s'
              % (wspath, ws.version,
                 'self-locating' if ws.self_locating
                 else 'NOT self-locating; it declares which table, not where (R82.3)'))
    tables = None
    if '--schema' in sys.argv:
        i = sys.argv.index('--schema')
        paths = sys.argv[i + 1].split(',')
        tables = load_schemas(paths)
        args = [a for a in args if a not in paths]
    for a in args:
        report(a, profs, tables, ws)
