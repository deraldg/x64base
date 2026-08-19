#!/usr/bin/env python3
"""A SECOND BACKEND: generate HTML from a UIDEF table. AIF-120.

Gate 11 (R28) tested whether a second AUTHOR could build a consumer from the
contract. This tests something else: whether the format survives a different
GEOMETRY MODEL. Tk gave place, pack and grid -- all pixels. A browser flows boxes,
and the contract's own section 5 names it as a candidate target for exactly that
reason. If `FLOW` is really the portable geometry, it has to land here without the
table changing.

Same author as `uidef_tk.py`, and that is stated rather than glossed: this is a
portability test, not an independence test. R28 was the independence test.
"""
import os, sys, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# `read_vfp_binary` is the VFP binary reader and it lives in tools/vfp.
# tools/uidef/read_vfp_binary.py is a GITIGNORED working copy, so importing it
# from this directory made nine committed tools unimportable on a fresh clone --
# found by the house 'sweep for your own leftovers' rule, not by anything failing.
# tools/vfp goes on the path FIRST so the ignored copy can never shadow it.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vfp'))
from read_vfp_binary import Dbf

# The profile this target declares, for manifest.py to import (R24.1).
KINDS_RENDERED = frozenset((
    'form', 'label', 'text', 'button', 'check', 'radio', 'list', 'combo',
    'image', 'panel', 'page', 'group', 'pageset',
))
FLOWS_SUPPORTED = frozenset(('row', 'column', 'grid', 'free'))
DISPATCH_SUPPORTED = frozenset(('ui', 'worker', 'host'))
# A browser provides MORE host capabilities than Tk: find and replace are native.
CAPABILITIES = (
    'edit.cut', 'edit.copy', 'edit.paste', 'edit.clear', 'edit.select_all',
    'edit.undo', 'edit.redo', 'edit.find',
)

# R25: a bound control's width follows its mask. In a browser the honest unit is
# characters, not pixels -- `ch` is exactly "one zero-width", which is what a mask
# position is. So R25's SLOPE does not travel and its MECHANISM does.
CONTENT_SIZED = {'label', 'button', 'check', 'radio', 'group', 'page', 'form'}


def parse_props(txt):
    out = {}
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if ' = ' in line:
            k, v = line.split(' = ', 1)
            out[k.strip().lower()] = v.strip().strip('"')
    return out


def parse_handlers(txt):
    out = []
    for line in (txt or '').replace('\r\n', '\n').split('\n'):
        if '=' not in line:
            continue
        ev, rest = line.split('=', 1)
        comp = None
        if '->' in rest:
            rest, comp = rest.split('->', 1)
        parts = [p.strip() for p in rest.split('/')]
        out.append((ev.strip(), parts[0], (parts[1] if len(parts) > 1 else 'ui').lower()))
    return out


def load(path):
    rows = list(Dbf(path).rows())
    kind = lambda k: [r for r in rows if (r['RECKIND'] or '').strip() == k]
    return kind('DOC')[0], kind('FONT'), kind('OBJ')


def generate(path):
    doc, fonts, objs = load(path)
    rec = {(r['OBJID'] or '').strip(): r for r in objs}
    kids = {}
    for r in objs:
        kids.setdefault((r['PARENT'] or '').strip(), []).append(r)
    for k in kids:
        kids[k].sort(key=lambda r: int((r['ORDINAL'] or '0').strip() or 0))

    notes = []
    fontcss = {}
    for i, f in enumerate(fonts, 1):
        fp = parse_props(f['PROPS'])
        if fp.get('name') and fp.get('size'):
            fontcss[i] = "font-family:%s;font-size:%spt" % (fp['name'], fp['size'])

    def esc(t):
        return html.escape(t or '')

    def style_for(r, kind, org, parent_flow, parent_kind):
        st = []
        fr = int(float((r['FONTREF'] or '0').strip() or 0))
        if fr:
            if fr in fontcss:
                st.append(fontcss[fr])
            else:
                notes.append("FONTREF %d on %s names no usable FONT row"
                             % (fr, (r['OBJID'] or '').strip()))
        if parent_flow == 'free' and 'origin_top' in org and 'origin_left' in org:
            st.append("position:absolute;top:%spx;left:%spx"
                      % (org['origin_top'], org['origin_left']))
            if 'origin_width' in org and kind not in CONTENT_SIZED:
                st.append("width:%spx" % org['origin_width'])   # R16
        # Contract s5: SPAN gives the cells a member consumes in a `grid` flow.
        # CSS grid has the concept natively, which is a point for FLOW being the
        # portable geometry rather than a Tk convenience.
        if parent_flow == 'grid':
            span = int(float((r['SPAN'] or '0').strip() or 0)) or 1
            if span > 1:
                st.append("grid-column:span %d" % span)
        mask = parse_props(r['PROPS']).get('mask')
        if mask and kind not in CONTENT_SIZED:
            # R25's mechanism, in the unit this target actually has.
            st.append("width:%dch" % (len(mask) + 1))
        return ";".join(st)

    def container_style(oid, flow, pr):
        if flow == 'row':
            return "display:flex;flex-direction:row;gap:6px;align-items:center"
        if flow == 'column':
            return "display:flex;flex-direction:column;gap:4px;align-items:flex-start"
        if flow == 'grid':
            if 'columns' not in pr:
                notes.append("REFUSED grid on %s -- FLOW=grid with no Columns "
                             "property (R23.2)" % oid)
                return "display:flex;flex-direction:column;gap:4px;align-items:flex-start"
            return ("display:grid;grid-template-columns:repeat(%s,max-content);"
                    "gap:4px 8px;align-items:center" % pr['columns'])
        if flow == 'free':
            kidsl = kids.get(oid, [])
            if kidsl and not any((c['ORIGIN'] or '').strip() for c in kidsl):
                notes.append("DERIVED layout for %s -- FLOW=free with no ORIGIN on "
                             "any child; fell back to ORDINAL order (R23.3)" % oid)
                return "display:flex;flex-direction:column;gap:4px;align-items:flex-start"
            return "position:relative;min-height:%spx" % (
                parse_props(rec[oid]['ORIGIN']).get('origin_height', '0')
                if oid in rec else '0')
        return ""

    out = []
    counts = {'made': 0, 'refused': 0, 'host_ok': 0, 'host_no': 0}

    def emit(r, parent_flow, parent_kind, depth):
        oid = (r['OBJID'] or '').strip()
        kind = (r['KIND'] or '').strip().lower()
        pr = parse_props(r['PROPS'])
        org = parse_props(r['ORIGIN'])
        flow = (r['FLOW'] or '').strip().lower()
        cap = pr.get('caption', '')
        pad = '  ' * depth
        if kind not in KINDS_RENDERED:
            out.append('%s<!-- REFUSED kind %s on %s (contract s4) -->' % (pad, kind, oid))
            counts['refused'] += 1
            notes.append("REFUSED kind %r on %s -- contract s4" % (kind, oid))
            return
        counts['made'] += 1
        st = style_for(r, kind, org, parent_flow, parent_kind)
        # R27: TABORDINAL is a second ordinal over the same children. A browser has
        # exactly that concept and spells it `tabindex`.
        tab = ''
        t = str(r['TABORDINAL'] or '').strip()
        if t and t != '0':
            tab = ' tabindex="%s"' % int(float(t))
        # R20/R22.4: a `host` item is wired if this target provides the capability,
        # and refused BY NAME if it does not.
        onclick = ''
        for ev, name, disp in parse_handlers(r['HANDLERS']):
            if ev != 'Click':
                continue
            if disp == 'host':
                if name in CAPABILITIES:
                    counts['host_ok'] += 1
                    onclick = ' onclick="hostcap(\'%s\')"' % name
                else:
                    counts['host_no'] += 1
                    notes.append("REFUSED capability %s on %s -- this target does "
                                 "not provide it (R20, R22.4)" % (name, oid))
                    cap = cap + "  [no host capability: %s]" % name
                    onclick = ' disabled'
        cs = container_style(oid, flow, pr) if flow else ''
        full = ";".join(x for x in (st, cs) if x)
        sattr = ' style="%s"' % full if full else ''
        child = kids.get(oid, [])

        if kind == 'form':
            out.append('%s<div class="form"%s>' % (pad, sattr))
            if cap:
                out.append('%s  <h1>%s</h1>' % (pad, esc(cap)))
        elif kind == 'label':
            out.append('%s<label%s%s>%s</label>' % (pad, sattr, tab, esc(cap)))
        elif kind == 'text':
            out.append('%s<input type="text"%s%s>' % (pad, sattr, tab))
        elif kind == 'button':
            out.append('%s<button%s%s%s>%s</button>' % (pad, sattr, tab, onclick, esc(cap)))
        elif kind in ('check', 'radio'):
            ty = 'checkbox' if kind == 'check' else 'radio'
            out.append('%s<label%s><input type="%s"%s> %s</label>'
                       % (pad, sattr, ty, tab, esc(cap)))
        elif kind == 'combo':
            out.append('%s<select%s%s></select>' % (pad, sattr, tab))
        elif kind == 'list':
            out.append('%s<select multiple size="4"%s%s></select>' % (pad, sattr, tab))
        elif kind == 'image':
            out.append('%s<div class="img"%s>[image]</div>' % (pad, sattr))
        elif kind == 'group':
            out.append('%s<fieldset%s><legend>%s</legend>' % (pad, sattr, esc(cap)))
        elif kind == 'pageset':
            out.append('%s<div class="tabs"%s>' % (pad, sattr))
        elif kind == 'page':
            out.append('%s<details open><summary>%s</summary><div%s>'
                       % (pad, esc(cap) or oid, sattr))
        else:
            out.append('%s<div%s>' % (pad, sattr))

        for c in child:
            emit(c, flow, kind, depth + 1)

        if kind == 'group':
            out.append('%s</fieldset>' % pad)
        elif kind == 'page':
            out.append('%s</div></details>' % pad)
        elif kind in ('form', 'pageset', 'panel'):
            out.append('%s</div>' % pad)

    for r in kids.get('', []):
        emit(r, '', '', 1)

    dp = parse_props(doc['PROPS'])
    page = ["<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
            "<title>%s</title>" % esc(dp.get('sourcefile', 'UIDEF')),
            "<style>body{font-family:sans-serif;font-size:9pt;margin:12px}",
            ".form{border:1px solid #999;padding:10px;display:inline-block}",
            "fieldset{border:1px solid #aaa;margin:2px 0}",
            "details{border:1px solid #ccc;padding:2px 6px;margin:2px 0}",
            "button[disabled]{color:#999}",
            ".img{border:1px dashed #999;padding:6px;color:#666}</style>",
            "<script>function hostcap(c){document.execCommand("
            "{'edit.cut':'cut','edit.copy':'copy','edit.paste':'paste',"
            "'edit.undo':'undo','edit.redo':'redo','edit.clear':'delete',"
            "'edit.select_all':'selectAll'}[c]||c)}</script>",
            "</head><body>"] + out + ["</body></html>"]
    return "\n".join(page), notes, counts


if __name__ == '__main__':
    doc, notes, counts = generate(sys.argv[1])
    outp = sys.argv[2] if len(sys.argv) > 2 else None
    if outp:
        open(outp, 'w', encoding='utf-8').write(doc)
    print("%s -> %s" % (os.path.basename(sys.argv[1]), outp or '(stdout)'))
    print("  elements %d   refused kinds %d   host capabilities wired %d, refused %d"
          % (counts['made'], counts['refused'], counts['host_ok'], counts['host_no']))
    for n in notes:
        print("  " + n)
    if not outp:
        print(doc)
