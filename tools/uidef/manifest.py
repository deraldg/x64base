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
    }
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
        span = (r['SPAN'] or '').strip()
        if span and span not in ('0', '1'):
            m['spans'].append((oid, span))
        if (r['BINDING'] or '').strip():
            m['bindings'] += 1
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
    if m['bindings']:
        out.append(('REQUIRE', '%d bound control(s)' % m['bindings'],
                    'target must supply a data source; widths come from the schema (R17)'))
    return out


def report(path, profiles):
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
    print()
    return m


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    profs = []
    if '--minimal' in sys.argv or '--both' in sys.argv:
        profs.append(PROFILE_MINIMAL)
    if '--minimal' not in sys.argv:
        profs.insert(0, profile_tk())
    for a in args:
        report(a, profs)
