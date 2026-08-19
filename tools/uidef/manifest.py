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


def schema_of(dbf_path):
    t = Dbf(dbf_path)
    return {name.lower(): (typ, width, dec) for name, typ, width, dec in t.fields}


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
    for oid, kind, binding, org_w, mask in m['bound']:
        if '.' not in binding:
            out.append(('REFUSE', 'BINDING %s on %s' % (binding, oid),
                        'not alias.field'))
            continue
        alias, field = binding.split('.', 1)
        sch = tables.get(alias.lower())
        if sch is None:
            continue                      # already refused above
        f = sch.get(field.lower())
        if f is None:
            out.append(('REFUSE', 'BINDING %s on %s' % (binding, oid),
                        'field not in the schema'))
            continue
        typ, width, dec = f
        want = KIND_WANTS.get(kind)
        if want and typ not in want:
            out.append(('REFUSE', '%s %s bound to %s' % (kind, oid, binding),
                        'field type %s cannot drive a %s' % (typ, kind)))
            continue
        px = R17_SLOPE * width + R17_INTERCEPT          # R17, from the field
        mx = mask_width(mask, typ)                      # R25, from the mask
        if org_w:
            widths.append((oid, binding, width, px, mx, org_w))
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
    }
    for r in rows:
        if (r['RECKIND'] or '').strip() == 'DOC':
            src = parse_props(r['SOURCE'])
            if src.get('alias'):
                m['aliases'][src['alias'].lower()] = src.get('table', '')
    referenced = set()
    for r in objs:
        oid = (r['OBJID'] or '').strip()
        kind = (r['KIND'] or '').strip().lower()
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
    if m['tab_absent'] and not m['tab_declared']:
        out.append(('DERIVE', '%d control(s) with no TABORDINAL' % m['tab_absent'],
                    'tab order must be derived and declared; measured, a derived '
                    'order matches the document exactly in 25.7% of groups'))
    elif m['tab_absent'] and m['tab_declared']:
        out.append(('DERIVE', '%d of %d control(s) lack TABORDINAL'
                    % (m['tab_absent'], m['tab_absent'] + m['tab_declared']),
                    'a partial tab order is the worst case: the gaps must be '
                    'derived and interleaved with the declared stops'))
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


def report(path, profiles, tables=None):
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
    tables = None
    if '--schema' in sys.argv:
        i = sys.argv.index('--schema')
        paths = sys.argv[i + 1].split(',')
        tables = load_schemas(paths)
        args = [a for a in args if a not in paths]
    for a in args:
        report(a, profs, tables)
